package com.yori.commands;

import java.util.HashMap;
import java.util.List;

import com.jagrosh.jdautilities.commandclient.Command;
import com.jagrosh.jdautilities.commandclient.CommandEvent;
import com.yori.vr.handlers.myAudioRecieveHandler;
import com.yori.vr.handlers.myAudioSendHandler;
import com.yori.vr.utils.Rift;

import net.dv8tion.jda.core.Permission;
import net.dv8tion.jda.core.entities.MessageChannel;
import net.dv8tion.jda.core.entities.VoiceChannel;
import net.dv8tion.jda.core.managers.AudioManager;
import net.dv8tion.jda.core.entities.Guild;

public class StartCommand extends Command 
{
	private HashMap<String, Rift> rifts;
	
	public StartCommand(HashMap<String, Rift> rifts)
	{
		this.rifts = rifts;
		this.name = "Start";
		this.userPermissions = new Permission[]{Permission.ADMINISTRATOR};
	}
	
	@Override
	protected void execute(CommandEvent event) 
	{
		String argsString = event.getArgs();
		String args[] = argsString.split(" ");
		MessageChannel messageChannel = event.getChannel();
		Guild guild = event.getGuild();
		
		if (args.length != 2) 
		{
			messageChannel.sendMessage("Please specify voice rift name and rift channel").queue();
			return;
		}
		
		String riftName = args[0];
		String riftChannelString = args[1];
		
		if (rifts.containsKey(riftName))
		{
			messageChannel.sendMessage("Rift in use please specify a new voice rift or use join").queue();
			return;
		}
		List<VoiceChannel> channelsMatching = event.getGuild().getVoiceChannelsByName(riftChannelString, true);
		if (channelsMatching.size() < 1)
		{
			messageChannel.sendMessage("Channel not found please specify a voice channel").queue();
			return;
		}
		
		VoiceChannel voiceChannel = channelsMatching.get(0);
		
		Rift rift = new Rift(voiceChannel);
		rift.setGuild1(guild);
		rifts.put(riftName, rift);
	  
		myAudioRecieveHandler reciever = new myAudioRecieveHandler(riftName, voiceChannel, rifts);
	  	myAudioSendHandler sender = new myAudioSendHandler(riftName, voiceChannel, rifts);
	  
	  	AudioManager audioManager = guild.getAudioManager();
	  
	  	audioManager.openAudioConnection(voiceChannel);
	  	audioManager.setReceivingHandler(reciever);
	  	audioManager.setSendingHandler(sender);
	  	event.getChannel().sendMessage("Voice Rift Opened").queue();
		
	}

}

