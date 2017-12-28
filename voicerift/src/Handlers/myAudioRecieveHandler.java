package Handlers;

import Utils.Rift;
import Utils.Rifts;
import net.dv8tion.jda.core.audio.CombinedAudio;
import net.dv8tion.jda.core.entities.Channel;

public class myAudioRecieveHandler implements net.dv8tion.jda.core.audio.AudioReceiveHandler
{
  private String riftName;
  private Channel channel;
  
  public myAudioRecieveHandler(String riftName, Channel channel)
  {
    this.riftName = riftName;
    this.channel = channel;
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
	  Rift rift = Rifts.rifts.get(riftName);

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