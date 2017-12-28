import Listeners.myEventListener;
import Utils.Rifts;
import javax.security.auth.login.LoginException;
import net.dv8tion.jda.core.AccountType;
import net.dv8tion.jda.core.JDA;
import net.dv8tion.jda.core.JDABuilder;
import net.dv8tion.jda.core.exceptions.RateLimitedException;



public class Main
{
  public static JDA jda;
  public static final String BOT_Token = "***REMOVED***";
   
  public static void main(String[] args)
    throws LoginException, IllegalArgumentException, InterruptedException, RateLimitedException
  {
    jda = new JDABuilder(AccountType.BOT).addEventListener(new Object[] { new myEventListener() }).setToken(BOT_Token).buildBlocking();
    @SuppressWarnings("unused")
	Rifts rifts = new Rifts();
  }
}