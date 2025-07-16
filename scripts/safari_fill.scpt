on run argv
    if (count of argv) is less than 3 then
        return "usage: safari_fill.scpt url selector text"
    end if
    set targetUrl to item 1 of argv
    set cssSelector to item 2 of argv
    set textValue to item 3 of argv

    tell application "Safari"
        activate
        set foundTab to false
        repeat with w in every window
            repeat with t in every tab of w
                if (URL of t) is targetUrl then
                    set current tab of w to t
                    set index of w to 1
                    set foundTab to true
                    exit repeat
                end if
            end repeat
            if foundTab then exit repeat
        end repeat
        if not foundTab then
            if (count of windows) is 0 then
                make new document
            end if
            set newTab to make new tab at end of tabs of window 1
            set URL of newTab to targetUrl
            set current tab of window 1 to newTab
        end if
        delay 1
        do JavaScript "var el=document.querySelector('" & cssSelector & "');if(el){el.focus();el.value='" & textValue & "';}" in current tab of window 1
    end tell
end run
