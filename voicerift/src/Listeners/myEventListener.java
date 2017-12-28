package Listeners;



import java.util.Arrays;
import java.util.HashMap;
import java.util.List;

import com.yori.vr.handlers.myAudioRecieveHandler;
import com.yori.vr.handlers.myAudioSendHandler;
import com.yori.vr.utils.Rift;

import net.dv8tion.jda.core.entities.Guild;
import net.dv8tion.jda.core.entities.Message;
import net.dv8tion.jda.core.entities.VoiceChannel;
import net.dv8tion.jda.core.events.message.guild.GuildMessageReceivedEvent;
import net.dv8tion.jda.core.managers.AudioManager;

public class myEventListener extends net.dv8tion.jda.core.hooks.ListenerAdapter
{
	public myEventListener() {}
  
	public void onGuildMessageReceived(GuildMessageReceivedEvent e)
	{
		Message message = e.getMessage();
		String msgArr[] = message.getContentRaw().split(" ");
		String command = msgArr[0];
		String args[] = Arrays.copyOfRange(msgArr, msgArr.length > 1 ? 1:0 , msgArr.length > 1 ? msgArr.length:1);
		Guild guild = e.getGuild();
		
		if (command.equals("*start"))
		{
			if (args.length != 2) 
			{
				e.getChannel().sendMessage("Please specify rift name and rift channel").queue();
				return;
			}
			
			String riftName = args[0];
			
			if (com.yori.vr.utils.Rifts.rifts.containsKey(riftName))
			{
				e.getChannel().sendMessage("Rift already in use").queue();
				return;
			}
			
			String channelName = args[1];
			List<VoiceChannel> voiceChannelList = guild.getVoiceChannelsByName(channelName, true);
			
			if (voiceChannelList.size() < 1)
			{
				e.getChannel().sendMessage("That is not a valid channel").queue();
				return;
			}
		  
			VoiceChannel voiceChannel = voiceChannelList.get(0);
				  
			Rift rift = new Rift(voiceChannel);
			rift.setGuild1(guild);
			com.yori.vr.utils.Rifts.rifts.put(riftName, rift);
		  
			myAudioRecieveHandler reciever = new myAudioRecieveHandler(riftName, voiceChannel);
		  	myAudioSendHandler sender = new myAudioSendHandler(riftName, voiceChannel);
		  
		  	AudioManager audioManager = guild.getAudioManager();
		  
		  	audioManager.openAudioConnection(voiceChannel);
		  	audioManager.setReceivingHandler(reciever);
		  	audioManager.setSendingHandler(sender);
		  	e.getChannel().sendMessage("Voice Rift Opened").queue();
		}
	  
		if (command.equals("*join"))
		{
			if (args.length != 2) 
			{
				e.getChannel().sendMessage("Please specify rift name and rift channel").queue();
				return;
			}
		  
			String riftName = args[0];
		  
			if (!com.yori.vr.utils.Rifts.rifts.containsKey(riftName))
			{
				e.getChannel().sendMessage("That is not a valid rift").queue();
				return;
			}
			String channelName = args[1];
			List<VoiceChannel> voiceChannelList = guild.getVoiceChannelsByName(channelName, true);
		  
			if (voiceChannelList.size() < 1)
			{
				e.getChannel().sendMessage("That is not a valid channel").queue();
				return;
			}
		  
			VoiceChannel voiceChannel = voiceChannelList.get(0);
		 
		  
			Rift rift = com.yori.vr.utils.Rifts.rifts.get(riftName);
			rift.setGuild2(guild);
			rift.join(voiceChannel);
			myAudioRecieveHandler reciever = new myAudioRecieveHandler(riftName, voiceChannel);
			myAudioSendHandler sender = new myAudioSendHandler(riftName, voiceChannel);
		  
			AudioManager audioManager = guild.getAudioManager();
		  
			audioManager.openAudioConnection(voiceChannel);
			audioManager.setReceivingHandler(reciever);
			audioManager.setSendingHandler(sender);
			e.getChannel().sendMessage("Voice Rift Joined").queue();
		}
		
		if (command.equals("*close"))
		{
			String riftName = args[0];
			if (args.length != 1)
			{
				e.getChannel().sendMessage("Please enter a valid rift name").queue();
				return;
			}
			
			HashMap<String, Rift> rifts = com.yori.vr.utils.Rifts.rifts;
			if(!rifts.containsKey(riftName))
			{
				e.getChannel().sendMessage("Please enter a valid rift name").queue();
				return;
			}
			
			Rift rift = rifts.get(riftName);
			rift.getGuild1().getAudioManager().closeAudioConnection();
			rift.getGuild2().getAudioManager().closeAudioConnection();
			rifts.remove(riftName);
			
			
			
			
			
			
			
		}
	} 
}