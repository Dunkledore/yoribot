package com.yori.vr.handlers;

import java.util.HashMap;

import com.yori.vr.utils.Rift;

import net.dv8tion.jda.core.audio.CombinedAudio;
import net.dv8tion.jda.core.entities.Channel;

public class myAudioRecieveHandler implements net.dv8tion.jda.core.audio.AudioReceiveHandler
{
  private String riftName;
  private Channel channel;
  private HashMap<String, Rift> rifts;
  
  public myAudioRecieveHandler(String riftName, Channel channel, HashMap<String, Rift> rifts)
  {
    this.riftName = riftName;
    this.channel = channel;
    this.rifts = rifts;
  }
  
  public boolean canReceiveCombined()
  {
    return true;
  }

  public boolean canReceiveUser()
  {
    return false;
  }
  
  public void handleCombinedAudio(CombinedAudio combinedAudio)
  {
	  Rift rift = rifts.get(riftName);

      if (channel.equals(rift.getChannel1()))
      {
    	  rift.setServer1Audio(combinedAudio.getAudioData(0.5D));
      }
      if (channel.equals(rift.getChannel2()))
      {
    	  rift.setServer2Audio(combinedAudio.getAudioData(0.5D));
	  }

  }
  
  public void handleUserAudio(net.dv8tion.jda.core.audio.UserAudio userAudio) 
  {
	  
  }
}