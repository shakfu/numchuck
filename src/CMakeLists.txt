# set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_RELEASE ${CMAKE_SOURCE_DIR}/src/pychuck)
# set(CMAKE_INSTALL_PREFIX ${CMAKE_SOURCE_DIR}/src/pychuck)

nanobind_add_module(
  # Name of the extension
  _pychuck

  # Target the stable ABI for Python 3.12+, which reduces
  # the number of binary wheels that must be built. This
  # does nothing on older Python versions
  STABLE_ABI

  # Build libnanobind statically and merge it into the
  # extension (which itself remains a shared library)
  #
  # If your project builds multiple extensions, you can
  # replace this flag by NB_SHARED to conserve space by
  # reusing a shared libnanobind across libraries
  NB_STATIC

  # Source code goes here
  ${CMAKE_SOURCE_DIR}/src/_pychuck.cpp
  ${CMAKE_SOURCE_DIR}/thirdparty/chuck/host/chuck_audio.cpp
  ${CMAKE_SOURCE_DIR}/thirdparty/chuck/host/RtAudio/RtAudio.cpp
)

target_compile_options(_pychuck
    PUBLIC
    $<$<PLATFORM_ID:Linux>:-fno-strict-aliasing>
    $<$<PLATFORM_ID:Linux>:-fPIC>
)

# Define platform-specific RtAudio macros
target_compile_definitions(_pychuck
    PRIVATE
    $<$<PLATFORM_ID:Darwin>:__MACOSX_CORE__>
    $<$<PLATFORM_ID:Windows>:__PLATFORM_WIN32__>
    $<$<PLATFORM_ID:Windows>:__WINDOWS_DS__>
    $<$<PLATFORM_ID:Linux>:__LINUX_ALSA__> # default to __ALSA__
    $<$<AND:$<PLATFORM_ID:Linux>,$<BOOL:${LINUX_ALSA}>>:__LINUX_ALSA__>
    $<$<AND:$<PLATFORM_ID:Linux>,$<BOOL:${LINUX_PULSE}>>:__LINUX_PULSE__>
    $<$<AND:$<PLATFORM_ID:Linux>,$<BOOL:${LINUX_JACK}>>:__UNIX_JACK__>
    $<$<PLATFORM_ID:Linux>:__CK_SNDFILE_NATIVE__>
    HAVE_CONFIG_H
)

target_include_directories(_pychuck
    PRIVATE
    ${CMAKE_SOURCE_DIR}/thirdparty/chuck/core
    ${CMAKE_SOURCE_DIR}/thirdparty/chuck/host
    ${CMAKE_SOURCE_DIR}/thirdparty/chuck/host/RtAudio
    ${CMAKE_SOURCE_DIR}/thirdparty/chuck/host/RtAudio/include
)

target_link_libraries(_pychuck
    PUBLIC
    "$<$<PLATFORM_ID:Darwin>:-framework CoreAudio>"
    "$<$<PLATFORM_ID:Darwin>:-framework CoreMIDI>"
    "$<$<PLATFORM_ID:Darwin>:-framework CoreFoundation>"
    "$<$<PLATFORM_ID:Darwin>:-framework IOKit>"
    "$<$<PLATFORM_ID:Darwin>:-framework Carbon>"
    "$<$<PLATFORM_ID:Darwin>:-framework AppKit>"
    "$<$<PLATFORM_ID:Darwin>:-framework Foundation>"
    "$<$<PLATFORM_ID:Darwin>:-F/System/Library/PrivateFrameworks>"
    "$<$<PLATFORM_ID:Darwin>:-weak_framework MultitouchSupport>"
    $<$<PLATFORM_ID:Linux>:-lasound>
    $<$<PLATFORM_ID:Linux>:-lstdc++>
    $<$<PLATFORM_ID:Linux>:-ldl>
    $<$<PLATFORM_ID:Linux>:-lm>
    $<$<PLATFORM_ID:Linux>:-lsndfile>
    $<$<PLATFORM_ID:Linux>:-lpthread>
    $<$<AND:$<PLATFORM_ID:Linux>,$<BOOL:${LINUX_JACK}>>:-ljack>
    $<$<AND:$<PLATFORM_ID:Linux>,$<BOOL:${LINUX_PULSE}>>:-lpulse-simple>
    $<$<AND:$<PLATFORM_ID:Linux>,$<BOOL:${LINUX_PULSE}>>:-lpulse>
    chuck_lib
)

# Link static chugins when CM_STATIC_CHUGINS is enabled
if(CM_STATIC_CHUGINS)
    # Core chugins (always available)
    # Note: Some chugins have conflicting symbols and cannot be linked together:
    #   - PitchTrack vs Sigmund (both have mayer FFT) - keeping Sigmund
    #   - Multicomb vs Spectacle (both have Odelay) - keeping Multicomb
    set(STATIC_CHUGINS
        ABSaturator
        AmbPan
        Binaural
        Bitcrusher
        ConvRev
        Elliptic
        ExpDelay
        ExpEnv
        FIR
        FoldbackSaturator
        GVerb
        KasFilter
        Ladspa
        Line
        MagicSine
        Mesh2D
        MIAP
        Multicomb
        NHHall
        Overdrive
        PanN
        Patch
        Perlin
        # PitchTrack  # conflicts with Sigmund (duplicate mayer FFT symbols)
        PowerADSR
        Random
        Range
        RegEx
        Sigmund
        # Spectacle  # conflicts with Multicomb (duplicate Odelay symbols)
        Wavetable
        WinFuncEnv
        WPDiodeLadder
        WPKorg35
        XML
    )

    # Platform-specific chugins
    if(CMAKE_HOST_APPLE)
        list(APPEND STATIC_CHUGINS AudioUnit)
    endif()

    # Optional chugins (require external dependencies)
    # if(CM_ABLETONLINK)
    #     list(APPEND STATIC_CHUGINS AbletonLink)
    # endif()
    # if(CM_FAUST)
    #     list(APPEND STATIC_CHUGINS Fauck)
    # endif()
    # if(CM_FLUIDSYNTH)
    #     list(APPEND STATIC_CHUGINS FluidSynth)
    # endif()
    # if(CM_WARPBUF)
    #     list(APPEND STATIC_CHUGINS WarpBuf)
    # endif()

    # Force linker to include all symbols from static chugins
    # (chugins register via constructors, so no direct references exist)
    if(CMAKE_HOST_APPLE)
        # macOS: use -force_load for each static library
        foreach(chugin ${STATIC_CHUGINS})
            target_link_libraries(_pychuck PUBLIC -force_load $<TARGET_FILE:${chugin}>)
        endforeach()
        # Additional frameworks required by AudioUnit chugin
        target_link_libraries(_pychuck PUBLIC
            "-framework AudioToolbox"
            "-framework AudioUnit"
        )
    else()
        # Linux: use --whole-archive
        target_link_libraries(_pychuck PUBLIC
            -Wl,--whole-archive
            ${STATIC_CHUGINS}
            -Wl,--no-whole-archive
        )
    endif()

    message(STATUS "Linking static chugins: ${STATIC_CHUGINS}")
endif()


set_target_properties(_pychuck PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_SOURCE_DIR}/src/pychuck"
    ARCHIVE_OUTPUT_DIRECTORY_RELEASE "${CMAKE_SOURCE_DIR}/src/pychuck"
    LIBRARY_OUTPUT_DIRECTORY_RELEASE "${CMAKE_SOURCE_DIR}/src/pychuck"
)


# Install directive for scikit-build-core
install(TARGETS _pychuck LIBRARY DESTINATION pychuck)


