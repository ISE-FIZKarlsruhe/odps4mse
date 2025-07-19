@echo off
setlocal enabledelayedexpansion

REM Define the ontologies to process
set ONTOLOGIES=

REM Loop through all .owl and .ttl files in the Ontologies directory
for %%F in (Ontologies\*.owl Ontologies\*.ttl) do (
    set "ONTOLOGIES=!ONTOLOGIES! %%~nxF"
)

REM Show the result
echo ONTOLOGIES = %ONTOLOGIES%

REM Define the methods to run
set METHODS=STAR TOP BOT subset
set INTERMEDIATES=all minimal none

REM Loop through each ontology
for %%O in (%ONTOLOGIES%) do (
    
    REM Extract base name (e.g., pmdcore from pmdcore.ttl)
    for %%F in (%%O) do (
        set "ONT_NAME=%%~nF"
    )
    
    REM Find all term files in Terms/<ontology_name>/
    for %%T in (Terms/!ONT_NAME!\*.txt) do (
        REM Extract the term set name (e.g., process_steps from process_steps_terms.txt)
        for %%A in (%%~nT) do (
            set "TERM_FILENAME=%%~nA"
        )
        echo !TERM_FILENAME!
        REM Remove "_terms" from the filename to get term set name
        set "TERM_SET=!TERM_FILENAME!"

        REM Set output directory
        set "OUTPUT_DIR=Patterns/!ONT_NAME!\!TERM_SET!"

        REM Create output directory if it does not exist
        if not exist "!OUTPUT_DIR!" (
            mkdir "!OUTPUT_DIR!"
        )

        REM Run extract for all method/intermediate combinations
        for %%M in (%METHODS%) do (
            for %%I in (%INTERMEDIATES%) do (
            
                set "TERMFIXED=%%T"
                set "TERMFIXED=!TERMFIXED:\=/!"
                set "OUTPUT_FIXED=!OUTPUT_DIR:\=/!"
                echo Running %%M %%I on !ONT_NAME! using !TERM_SET! terms and term file !TERMFIXED! output /work/!OUTPUT_DIR!/!ONT_NAME!_%%M_%%I.ttl

                docker run -v "%CD%:/work" -w /work --rm -ti obolibrary/odkfull robot extract ^
                    --method %%M ^
                    --intermediates %%I ^
                    --input /work/Ontologies/%%O ^
                    --term-file "!TERMFIXED!" ^
                    --individuals exclude ^
                    --imports exclude ^
                    --annotate-with-source true ^
                    --output /work/!OUTPUT_FIXED!/!ONT_NAME!_%%M_%%I.ttl

                if !errorlevel! neq 0 (
                    echo Failed for !ONT_NAME! - !TERM_SET! - %%M %%I
                    pause
                    exit /b
                )

                echo Output saved to !OUTPUT_FIXED!\!ONT_NAME!_%%M_%%I.ttl
            )
        )
    )
)

echo All processing completed successfully.
pause