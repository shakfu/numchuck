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
    # # $<$<BOOL:${CM_STATIC_CHUGINS}>:AbletonLink>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:ABSaturator>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:AmbPan>
    # # $<$<BOOL:${CM_STATIC_CHUGINS}>:AudioUnit>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:Binaural>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:Bitcrusher>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:ConvRev>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:Elliptic>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:ExpDelay>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:ExpEnv>
    # # $<$<BOOL:${CM_STATIC_CHUGINS}>:Fauck>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:FIR>
    # # $<$<BOOL:${CM_STATIC_CHUGINS}>:FluidSynth>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:FoldbackSaturator>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:GVerb>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:KasFilter>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:Ladspa>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:Line>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:MagicSine>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:Mesh2D>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:MIAP>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:Multicomb>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:NHHall>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:Overdrive>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:PanN>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:Patch>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:Perlin>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:PitchTrack>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:PowerADSR>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:Random>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:Range>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:RegEx>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:Sigmund>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:Spectacle>
    # # $<$<BOOL:${CM_STATIC_CHUGINS}>:WarpBuf>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:Wavetable>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:WinFuncEnv>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:WPDiodeLadder>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:WPKorg35>
    # $<$<BOOL:${CM_STATIC_CHUGINS}>:XML>
)


set_target_properties(_pychuck PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_SOURCE_DIR}/src/pychuck"
    ARCHIVE_OUTPUT_DIRECTORY_RELEASE "${CMAKE_SOURCE_DIR}/src/pychuck"
    LIBRARY_OUTPUT_DIRECTORY_RELEASE "${CMAKE_SOURCE_DIR}/src/pychuck"
)


# Install directive for scikit-build-core
install(TARGETS _pychuck LIBRARY DESTINATION pychuck)


