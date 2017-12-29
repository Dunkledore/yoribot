package com.yori;
import java.awt.Color;
import java.io.IOException;
import java.util.HashMap;

import javax.security.auth.login.LoginException;

import com.jagrosh.jdautilities.commandclient.CommandClient;
import com.jagrosh.jdautilities.commandclient.CommandClientBuilder;
import com.jagrosh.jdautilities.commandclient.examples.AboutCommand;
import com.jagrosh.jdautilities.commandclient.examples.PingCommand;
import com.jagrosh.jdautilities.commandclient.examples.ShutdownCommand;
import com.jagrosh.jdautilities.waiter.EventWaiter;
import com.yori.commands.CloseCommand;
import com.yori.commands.JoinCommand;
import com.yori.commands.StartCommand;
import com.yori.vr.utils.Rift;

import net.dv8tion.jda.core.AccountType;
import net.dv8tion.jda.core.JDABuilder;
import net.dv8tion.jda.core.OnlineStatus;
import net.dv8tion.jda.core.Permission;
import net.dv8tion.jda.core.exceptions.RateLimitedException;

public class Yori
{
    
    @SuppressWarnings("deprecation")
	public static void main(String[] args) throws IOException, LoginException, IllegalArgumentException, RateLimitedException
    {
        // config.txt contains two lines
        //List<String> list = Files.readAllLines(Paths.get("config.txt"));

        // the first is the bot token
        //String token = args[0];
        String token = "MzgzMzQ1NjA5MTY5NTY3NzU0.DPi59A.dWx2UF904cQIHZkewpLLdlwwpaE"; //just to test

        // the second is the bot's owner's id
        //String ownerId = args[1];
        String ownerId = "123900100081745922";

        // define an eventwaiter, dont forget to add this to the JDABuilder!
        EventWaiter waiter = new EventWaiter();

        // define a command client
        CommandClientBuilder client = new CommandClientBuilder();
        client.setGame(null);

        // sets the owner of the bot
        client.setOwnerId(ownerId);

        // sets emojis used throughout the bot on successes, warnings, and failures
        client.setEmojis("\uD83D\uDE03", "\uD83D\uDE2E", "\uD83D\uDE26");

        // sets the bot prefix
        client.setPrefix("-");

        // add a list of rifts for voicerift commands
        HashMap<String, Rift> rifts = new HashMap<String, Rift>();
        
        // adds commands
        client.addCommands(
                // command to show information about the bot
                new AboutCommand(Color.BLUE, "an example bot",
                        new String[]{"Cool commands","Nice examples","Lots of fun!"},
                        new Permission[]{Permission.ADMINISTRATOR}),

                // command to start a voicerift
                new StartCommand(rifts),
                
                // command to join a voicerift
                new JoinCommand(rifts),

                // commmand to close a voicerift
                new CloseCommand(rifts),
                // command to check bot latency
                new PingCommand(),
             
                // command to shut off the bot
                new ShutdownCommand());

        CommandClient listener = client.build();
        // start getting a bot account set up
        JDABuilder JDABuilder = new JDABuilder(AccountType.BOT)
                // set the token
                .setToken(token)

                // set the game for when the bot is loading
                .setStatus(OnlineStatus.DO_NOT_DISTURB)
                .setGame(null)

                // add the listeners
                .addEventListener(waiter)
                .addEventListener(listener);  
                
        // start it up! d
        JDABuilder.buildAsync();
        		
    }
}