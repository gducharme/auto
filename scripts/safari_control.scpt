on run argv
    if (count of argv) is 0 then
        return "usage: safari_control.scpt command [args]"
    end if
    set cmd to item 1 of argv
    if cmd is "open" then
        if (count of argv) < 2 then return "missing url"
        set targetUrl to item 2 of argv
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
            return "OK"
        end tell
    else if cmd is "click" then
        if (count of argv) < 2 then return "missing selector"
        set theSelector to item 2 of argv
        tell application "Safari"
            do JavaScript "var el=document.querySelector('" & theSelector & "'); if(el){el.click();}" in current tab of window 1
            return "OK"
        end tell
    else if cmd is "fill" then
        if (count of argv) < 3 then return "missing args"
        set theSelector to item 2 of argv
        set valueStr to item 3 of argv
        tell application "Safari"
            do JavaScript "var el=document.querySelector('" & theSelector & "'); if(el){el.innerText='" & valueStr & "'; el.dispatchEvent(new Event('input'));}" in current tab of window 1
            return "OK"
        end tell
    else if cmd is "run_js" then
        if (count of argv) < 2 then return "missing js"
        set jsCode to item 2 of argv
        tell application "Safari"
            return do JavaScript jsCode in current tab of window 1
        end tell
    else if cmd is "close_tab" then
        tell application "Safari"
            if (count of windows) > 0 then
                close current tab of window 1
            end if
            return "OK"
        end tell
    else
        return "unknown command"
    end if
end run
