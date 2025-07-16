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
        set jsFunction to "function setPromptAndClickCode(text){" & ¬
            "const promptDiv=document.getElementById('prompt-textarea');" & ¬
            "if(!promptDiv){console.error('⚠️ No element found with id prompt-textarea');return;}" & ¬
            "promptDiv.textContent=text;" & ¬
            "promptDiv.dispatchEvent(new Event('input'));" & ¬
            "console.log('📥 prompt-textarea now contains:',promptDiv.textContent);" & ¬
            "const candidates=document.querySelectorAll('div.flex.items-center.justify-center');" & ¬
            "console.log('🔍 Found',candidates.length,'candidates:',candidates);" & ¬
            "const codeButton=Array.from(candidates).find(el=>{" & ¬
            "const t=el.innerText.trim();" & ¬
            "console.log('   • candidate text:',JSON.stringify(t));" & ¬
            "return t==='Code';});" & ¬
            "if(codeButton){" & ¬
            "codeButton.click();" & ¬
            "console.log('✅ Clicked the Code button!');" & ¬
            "}else{" & ¬
            "console.warn('❌ No matching Code button found—check the debug log above.');" & ¬
            "}}"
        set js to jsFunction & " setPromptAndClickCode('" & textValue & "'); 'OK';"
        set resultText to do JavaScript js in current tab of window 1
        return resultText
    end tell
end run
