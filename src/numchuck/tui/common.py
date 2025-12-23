"""
Shared TUI components for editor and REPL.

Provides base class with common functionality:
- ChucK instance management
- Session tracking
- Shared UI components (help, shreds table, log)
- Common key bindings
"""

from pathlib import Path

from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import ConditionalContainer, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension as D
from prompt_toolkit.filters import Condition
from prompt_toolkit.widgets import TextArea

from .._numchuck import ChucK, PARAM_SAMPLE_RATE
from .session import ChuckSession


def format_elapsed_time(elapsed_sec: float) -> str:
    """Format elapsed time in human-readable format.

    Args:
        elapsed_sec: Elapsed time in seconds

    Returns:
        Formatted string like "5.2s", "2m30.5s", or "1h05m"
    """
    if elapsed_sec < 60:
        return f"{elapsed_sec:.1f}s"
    elif elapsed_sec < 3600:
        mins = int(elapsed_sec / 60)
        secs = elapsed_sec % 60
        return f"{mins}m{secs:04.1f}s"
    else:
        hours = int(elapsed_sec / 3600)
        mins = int((elapsed_sec % 3600) / 60)
        return f"{hours}h{mins:02d}m"


def format_shred_name(full_name: str, max_len: int = 56) -> str:
    """Format shred name for display, showing parent/filename.

    Args:
        full_name: Full path or name of the shred
        max_len: Maximum length for the name

    Returns:
        Formatted name truncated to max_len
    """
    try:
        path = Path(full_name)
        if path.parent.name:
            name = f"{path.parent.name}/{path.name}"
        else:
            name = path.name
    except (ValueError, TypeError):
        name = full_name
    return name[:max_len]


def generate_shreds_table(
    shreds: dict,
    chuck,
    use_pipes: bool = False,
) -> str:
    """Generate formatted table of active shreds.

    Args:
        shreds: Dictionary of shred_id -> shred info
        chuck: ChucK instance for querying VM time and sample rate
        use_pipes: If True, use pipe separators; if False, use spaces

    Returns:
        Formatted table string
    """
    if not shreds:
        return "No active shreds"

    lines = []

    # Header
    if use_pipes:
        lines.append(
            "ID   | Name                                                    | Elapsed"
        )
        lines.append("-" * 78)
    else:
        lines.append(
            "ID    Name                                                    Elapsed"
        )
        lines.append("\u2500" * 78)  # Unicode box drawing character

    # Get current VM time for elapsed calculation
    try:
        current_time = chuck.now()
    except (RuntimeError, AttributeError):
        current_time = 0.0

    # Get sample rate
    try:
        sample_rate = chuck.get_param_int(PARAM_SAMPLE_RATE)
    except (RuntimeError, AttributeError, ValueError):
        sample_rate = 44100

    for shred_id, info in sorted(shreds.items()):
        name = format_shred_name(info["name"])

        # Calculate elapsed time in seconds
        spork_time = info.get("time", 0.0)
        elapsed_samples = current_time - spork_time
        elapsed_sec = elapsed_samples / sample_rate if sample_rate > 0 else 0.0
        time_str = format_elapsed_time(elapsed_sec)

        if use_pipes:
            lines.append(f"{shred_id:<5d} | {name:<56s} | {time_str}")
        else:
            lines.append(f"{shred_id:<5} {name:<56} {time_str}")

    return "\n".join(lines)


class ChuckApplication:
    """Base application managing ChucK instance and shared state."""

    def __init__(self, project_name=None):
        self.chuck = ChucK()
        self.session = ChuckSession(self.chuck, project_name=project_name)

        # Shared UI state
        self.show_help = False
        self.show_shreds = False
        self.show_log = False

        # Log tracking
        self.log_messages = []

    def get_common_key_bindings(self):
        """Common key bindings shared across editor and REPL."""
        kb = KeyBindings()

        @kb.add("c-q")
        def exit_app(event):
            """Exit application"""
            event.app.exit()

        @kb.add("f1")
        def toggle_help(event):
            """Toggle help window"""
            self.show_help = not self.show_help
            event.app.invalidate()

        @kb.add("f2")
        def toggle_shreds(event):
            """Toggle shreds table"""
            self.show_shreds = not self.show_shreds
            event.app.invalidate()

        @kb.add("f3")
        def toggle_log(event):
            """Toggle log window"""
            self.show_log = not self.show_log
            event.app.invalidate()

        return kb

    def create_help_window(self, help_text):
        """Create help window that toggles with F1."""
        help_area = TextArea(
            text=help_text,
            scrollbar=True,
            focusable=False,
            read_only=True,
            wrap_lines=True,
        )

        return ConditionalContainer(
            Window(
                content=help_area.control, height=D(min=10, max=30), wrap_lines=True
            ),
            filter=Condition(lambda: self.show_help),
        )

    def create_shreds_table(self):
        """Create shreds table that toggles with F2."""

        def get_text():
            return generate_shreds_table(
                self.session.shreds, self.chuck, use_pipes=True
            )

        return ConditionalContainer(
            Window(content=FormattedTextControl(get_text), height=D(min=5, max=15)),
            filter=Condition(lambda: self.show_shreds),
        )

    def create_log_window(self):
        """Create log window that toggles with F3."""
        log_area = TextArea(text="", scrollbar=True, focusable=False, read_only=True)

        def log_callback(msg):
            """Callback for ChucK output"""
            self.log_messages.append(msg)
            log_area.text += msg
            if len(self.log_messages) > 1000:
                # Trim old messages
                self.log_messages = self.log_messages[-500:]
                log_area.text = "".join(self.log_messages[-500:])

        # Set ChucK output callbacks
        self.chuck.set_chout_callback(log_callback)
        self.chuck.set_cherr_callback(log_callback)

        return ConditionalContainer(log_area, filter=Condition(lambda: self.show_log))

    def create_status_bar(self, status_text_func):
        """Create status bar at bottom of screen."""
        return Window(
            content=FormattedTextControl(status_text_func),
            height=1,
            style="bg:#444444 fg:#ffffff",
        )

    def cleanup(self):
        """Cleanup ChucK resources."""
        try:
            self.chuck.remove_all_shreds()
        except (RuntimeError, AttributeError):
            pass

        # Break circular references to allow proper garbage collection
        if hasattr(self, "session"):
            self.session.chuck = None
            del self.session
        if hasattr(self, "chuck"):
            del self.chuck
