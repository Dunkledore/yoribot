package Utils;

import lombok.Getter;
import lombok.Setter;
import net.dv8tion.jda.core.entities.Channel;
import net.dv8tion.jda.core.entities.Guild;

public class Rift 
{
	
  @Getter @Setter private byte[] server1Audio;
  @Getter @Setter private byte[] server2Audio;
  @Getter private Channel channel1;
  @Getter private Channel channel2;
  @Getter @Setter private Guild guild1;
  @Getter @Setter private Guild guild2;
    
  public Rift(Channel channel1)
  {
    this.channel1 = channel1;
  }
  
  public void join(Channel channel2)
  {
    this.channel2 = channel2;
  }
}