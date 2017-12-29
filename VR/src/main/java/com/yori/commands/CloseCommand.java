package com.yori.commands;

import java.util.HashMap;

import com.jagrosh.jdautilities.commandclient.Command;
import com.jagrosh.jdautilities.commandclient.CommandEvent;
import com.yori.vr.utils.Rift;

import net.dv8tion.jda.core.Permission;
import net.dv8tion.jda.core.entities.Guild;

public class CloseCommand extends Command 
{
	private HashMap<String, Rift> rifts;

	public CloseCommand(HashMap<String, Rift> rifts) 
	{
		this.rifts = rifts;
		this.name = "Close";
		this.userPermissions = new Permission[]{Permission.ADMINISTRATOR};
	}

	@Override
	protected void execute(CommandEvent event) 
	{
		String argsString = event.getArgs();
		String args[] = argsString.split(" ");
		String riftName = args[0];
		
		if (args.length != 1)
		{
			event.getChannel().sendMessage("Please enter a valid rift name").queue();
			return;
		}
		
		if(!rifts.containsKey(riftName))
		{
			event.getChannel().sendMessage("Please enter a valid rift name").queue();
			return;
		}
		
		Rift rift = rifts.get(riftName);
		rift.getGuild1().getAudioManager().closeAudioConnection();
		Guild guild2 = rift.getGuild2();
		if (guild2 != null)
		{
			guild2.getAudioManager().closeAudioConnection();
		}
		rifts.remove(riftName);
		
	}

}
