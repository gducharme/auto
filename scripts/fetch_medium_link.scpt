tell application "Mail"
    set theInbox to mailbox "INBOX" of account "iCloud"
    set msgs to (messages of theInbox whose read status is false and sender contains "no-reply@medium.com")
    if (count of msgs) > 0 then
        set theMsg to first item of msgs
        set theContent to content of theMsg
        set read status of theMsg to true
        return theContent
    else
        return ""
    end if
end tell
