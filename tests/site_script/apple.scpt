tell application "Safari"
    activate
    delay 0.2 -- allow Safari to come forward
    tell front document
        set js to "(function(){" & ¬
            "var btn = Array.from(document.querySelectorAll('button')).find(function(b){" & ¬
                "return b.textContent.trim() === 'Select from computer';" & ¬
            "});" & ¬
            "if (btn) {" & ¬
                "console.log('AppleScript: Select from computer button clicked');" & ¬
                "btn.click();" & ¬
                "return 'clicked';" & ¬
            "} else {" & ¬
                "console.log('AppleScript: Select from computer button NOT found');" & ¬
                "return 'not found';" & ¬
            "}" & ¬
        "})();"
        set resultText to do JavaScript js
    end tell
end tell
