This example demonstrates how to use `TelegramBot`.  
To get started provide your **bot token** to the bot and create some handlers to process user commands.  

Also, this example shows how to use a logger. This way error reports will be delivered directly to the admin
when any exceptions or errors are happening.  

The default handler here is included for messages that don't match any commands. 
If you don't use the default handler, users will receive an "Unknown command" response.  

You can run multiple bots within this application. Pass them as a list to the `add_bots` method.  

Further, refer to the other examples if you need managing (starting, stoping and printing statuses) of bots, using 
databases and ORM, configuring communication between remote applications or using **tasks** to invoke background 
scheduled events.  