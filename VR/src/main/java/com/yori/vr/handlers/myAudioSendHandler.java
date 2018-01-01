package com.yori.vr.handlers;

import java.util.HashMap;

import com.yori.vr.utils.Rift;
import net.dv8tion.jda.core.entities.Channel;
import net.dv8tion.jda.core.audio.AudioSendHandler;

public class myAudioSendHandler implements AudioSendHandler
{
  private String riftName;
  private Channel channel;
  private HashMap<String, Rift> rifts;
  
  public myAudioSendHandler(String riftName, Channel channel, HashMap<String, Rift> rifts)
  {
    this.riftName = riftName;
    this.channel = channel;
    this.rifts = rifts;
  }
  
  public boolean canProvide()
  {
    return true;
  }
  
  public byte[] provide20MsAudio()
  {
	 Rift rift = rifts.get(riftName);

     if (channel.equals(rift.getChannel1()))
     {
    	 return rift.getServer2Audio();
     }
     if (channel.equals(rift.getChannel2()))
     {
    	 return rift.getServer1Audio();
     }
   
     return null;
  }
}