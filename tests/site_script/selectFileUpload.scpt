-- SelectAndUpload.scpt
-- 1) Put the full POSIX path of your file here:
set theFilePath to "/Users/geoffreyducharme/Downloads/168740745.jpg"

tell application "System Events"
    delay 2
    -- 2) Make sure the Open dialog is frontmost
    tell process "Safari"
        set frontmost to true
    end tell
    delay 2

    -- 3) Type the path into the “Go to the folder” sheet:
    keystroke "G" using {shift down, command down}
    delay 0.2
    keystroke theFilePath
    delay 0.1
    keystroke return
    delay 0.2

    -- 4) Select the file (it should now be highlighted)
    keystroke return
    delay 0.2

    -- 5) Click the “Open” button
    --    (button 1 of the frontmost sheet is usually “Open”)
    tell process "Safari"
        tell front window
            click button 2 of sheet 1
        end tell
    end tell
end tell
