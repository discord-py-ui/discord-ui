:: Remove older versions
@rd /S /Q "./dist
@rd /S /Q "./build"
@rd /S /Q "./discord_ui.egg-info"

:: Build
py -m build
py -m twine upload dist/*