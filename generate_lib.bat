set DLL_PATH=%CONDA_PREFIX%\gurobi110.dll
set DEF_NAME=gurobi110.def
set LIB_NAME=gurobi110.lib
set OUTPUT_DIR=%~dpDLL_PATH%

:: Check if the DLL exists
if not exist "%DLL_PATH%" (
    echo Error: %DLL_PATH% not found.
    exit /b 1
)

:: Generate .def file from dumpbin output
dumpbin /exports "%DLL_PATH%" > temp_exports.txt

:: Extract relevant lines for the .def file
echo LIBRARY gurobi110 > %DEF_NAME%
echo EXPORTS >> %DEF_NAME%
findstr /r "^[0-9A-F]" temp_exports.txt | for /f "tokens=4" %%G in ('findstr /r "^[0-9A-F]" temp_exports.txt') do echo %%G >> %DEF_NAME%

:: Create .lib in the same directory as the DLL
lib /def:%DEF_NAME% /out:%OUTPUT_DIR%%LIB_NAME% /machine:x64

:: Verify .lib creation
if not exist "%OUTPUT_DIR%%LIB_NAME%" (
    echo Error: Failed to generate %LIB_NAME% next to the DLL.
    exit /b 1
)

:: Success message
echo Successfully generated %OUTPUT_DIR%%LIB_NAME%

:: Cleanup
del temp_exports.txt
