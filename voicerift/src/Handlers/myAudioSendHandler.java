package Handlers;

import Utils.Rift;
import Utils.Rifts;
import net.dv8tion.jda.core.entities.Channel;
import net.dv8tion.jda.core.audio.AudioSendHandler;

public class myAudioSendHandler implements AudioSendHandler
{
  private String riftName;
  private Channel channel;
  
  public myAudioSendHandler(String riftName, Channel channel)
  {
    this.riftName = riftName;
    this.channel = channel;
  }
  
  public boolean canProvide()
  {
    return true;
  }
  
  public byte[] provide20MsAudio()
  {
	 Rift rift = Rifts.rifts.get(riftName);

     if (channel.equals(rift.getChannel1()))
     {
    	 return rift.getServer2Audio();
     }
     if (channel.getId().equals(((Rift)Utils.Rifts.rifts.get(riftName)).getChannel2().getId()))
     {
    	 return rift.getServer1Audio();
     }
   
     return null;
  }
}