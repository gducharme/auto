tell application "Mail"
    set theInbox to mailbox "INBOX" of account "Google"
    set msgs to (messages of theInbox whose sender contains "noreply@medium.com")
    if (count of msgs) > 0 then
        set theMsg to first item of msgs
        set theContent to content of theMsg
        set read status of theMsg to true
        return theContent
    else
        return ""
    end if
end tell
