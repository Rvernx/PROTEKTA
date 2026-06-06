  GNU nano 8.7.1                                                                                  /var/ossec/active-response/bin/protekta-drop.sh                                                                                           
#!/bin/bash
# Read the alert data from Wazuh
read INPUT_JSON

# Extract the command (add/delete)
COMMAND=$(echo $INPUT_JSON | grep -oP '"command":"\K[^"]+' | head -n 1)

# Extract the IP using Suricata's specific field name (src_ip)
IP=$(echo $INPUT_JSON | grep -oP '"src_ip":"\K[^"]+' | head -n 1)

# If the IP is found, take action
if [ -n "$IP" ]; then
    if [ "$COMMAND" = "add" ]; then
        # 1. Ban the attacker (Rule #1)
        iptables -I INPUT -s $IP -j DROP
        
        # 2. Punch a hole for Wazuh Agent Heartbeat (Becomes new Rule #1 & #2)
        iptables -I INPUT -s $IP -p tcp --dport 1514 -j ACCEPT
        iptables -I INPUT -s $IP -p tcp --dport 1515 -j ACCEPT
        
        # Log the action for your project report
        echo "$(date) [LOCKDOWN]: Banned Attacker $IP" >> /var/ossec/logs/active-responses.log

    elif [ "$COMMAND" = "delete" ]; then
        # Clean up the rules when the ban expires
        iptables -D INPUT -s $IP -p tcp --dport 1515 -j ACCEPT 2>/dev/null
        iptables -D INPUT -s $IP -p tcp --dport 1514 -j ACCEPT 2>/dev/null
        iptables -D INPUT -s $IP -j DROP 2>/dev/null
        
        echo "$(date) [RELEASE]: Unbanned $IP" >> /var/ossec/logs/active-responses.log
    fi
fi

