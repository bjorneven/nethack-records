/*
  Things that need to be done
  - !Read data from disk as thread and communicate with drawThread so when a buffer reaches
    a certain size the read thread pauses until drawThread clears some space.  
  - !Do not reset file for each frame (if pos is further ahead in file), simply calculate diff and skip it.
  - Must catch other things than just Exception :)
  - Speed up drawing (ie double buffering and so on)
  - Add pretty buttons for playing and maybe optional font changing 
   (optionally using SoftFont from telnet applet: http://www.first.gmd.de/persons/leo/java/Telnet/
    if not, check for certain bytes not supported by font and replace them with more pleasurable substitutions.)
  - Manage to get past Excursionist as a tourist.

  Recent changes:
  Left deprecated Event handling in favor of actionlisteners.
  Fixed stop, play, next button. They all should work now.

  License: GPL (paste in long header here)
  VT emulation from Telnet applet and toInt bConv method taken from TTYPLAYER (java applet).

  Developers:
  Mic the Excursionist
  
 */

import java.applet.Applet;
import java.awt.*;
import java.awt.event.*;
import java.io.*;
import java.util.*;
import java.net.*;
import display.*;

public class AppletPlayer extends Applet{

    Terminal terminal = new vt320();
    InputStream iStream = null;
    Button prev = new Button("previous");
    Button play = new Button("play");
    Button stop = new Button("stop");
    Button next = new Button("next frame");
    Button nextb = new Button("next bytes");
    /* sleep, sleepInput = the number of milliseconds the drawthread sleeps between each frame/item in queue. */ 
    int sleep = 10, fc = 0, currentFrame = 0;
    TextField sleepInput = new TextField(Integer.toString(sleep));

    
    DrawThread drawThread;
    PlayThread playThread;

    String filename;
    Vector frameIndex = new Vector();

    public void init(){
        filename = getParameter("record");
        setLayout(new BorderLayout());        
        Panel control = new Panel();
        control.add(prev);
        control.add(stop);
        control.add(play);
        control.add(next);
        control.add(nextb);
        control.add(sleepInput);        
        add("North",control);
        setSize(640,480);
        add("Center", terminal);
        System.err.println("Codebase is");            
        terminal.putString("Aloha!\n");
        terminal.putString("\r Press play to the record of "+filename);
        InputStream tStream = null;
        try{
            System.err.println("Codebase is"+getCodeBase());            
            iStream = new BufferedInputStream(new URL(getCodeBase(),filename).openStream());
            iStream.mark(iStream.available()+1);            
            System.out.println(); 
            createFrameIndex();
        }catch(IOException e){
            System.out.println(e.getMessage());                    
            e.printStackTrace();
        }
        drawThread = new DrawThread(terminal,sleep);
        drawThread.start();
        playThread = new PlayThread(this);
        playThread.start();         
        reset();
        prev.addActionListener(
                               new ActionListener(){
                                   public void actionPerformed(ActionEvent e){
                                       System.out.println("prev"); 
                                       loadFrame(--currentFrame,false);
                                   }
                               }
                               );

        play.addActionListener(
                               new ActionListener(){
                                   public void actionPerformed(ActionEvent e){
                                       System.out.println("Play"); 
                                       playThread.begin(currentFrame); 
                                       drawThread.begin();   
                                   }
                               }
                               );

        stop.addActionListener(
                               new ActionListener(){
                                   public void actionPerformed(ActionEvent e){
                                       System.out.println("stop"); 
                                       currentFrame = playThread.halt(); 
                                       drawThread.halt();
                                   }
                               }
                               );

        next.addActionListener(
                               new ActionListener(){
                                   public void actionPerformed(ActionEvent e){
                                       System.out.println("next"); 
                                       if (loadFrame(currentFrame++,false)==-1)
                                           drawThread.halt();
                                       //                                       nextFrame(); 
                                       //                                       drawThread.next();
                                   }
                               }
                               );

        sleepInput.addActionListener(
                                     new ActionListener(){
                                         public void actionPerformed(ActionEvent e){
                                             System.out.println("Changing speed to "+sleepInput.getText()); 
                                             int newSleep = 0;
                                             try{
                                                 newSleep = Integer.parseInt(sleepInput.getText());
                                             }catch(NumberFormatException exception){
                                                 System.out.println("Error, not a valid number!");                                                 
                                             }                                             
                                             if (newSleep>=0)
                                                 playThread.setSleep(newSleep);
                                         }
                                     }
                                     );

        nextb.addActionListener(
                               new ActionListener(){
                                   public void actionPerformed(ActionEvent e){
                                       System.out.println("next"); 
                                       if (loadFrame(currentFrame++,true)==-1)
                                           drawThread.halt();
                                       //                                       printBytes(currentFrame++);
                                       //                                       nextFrame(); 
                                       //                                       drawThread.next();
                                   }
                               }
                               );
        
    }
    
    private void reset(){
        try{
            iStream.reset();
        }catch(IOException e){
            System.out.println("Error could not reset file. "+e.getMessage());
            e.printStackTrace();
        }
    }
    
    public void actionPerformed(ActionEvent e){
        System.out.println("Action performed "+e.getActionCommand());        
    }
    
    private void createFrameIndex(){        
        int fpos = 0;
        while(true){
            try{
                int len = 0; // The length in bytes of how many characters this frame will draw on-screen.
                int  pos = 0;
                int  nread = 0;
                byte[] buf = new byte[12]; // Frame info.
                while (pos < 12){
                    nread = iStream.read(buf, pos, 12-pos);
                    if (nread < 0)
                        break;
                    pos = pos + nread;
                    fpos+=nread;
                }
                if (nread < 0){
                    System.out.println("Number of frames "+fc);
                    System.out.println("Qs "+frameIndex.size());                    
                    break;
                }            
                len     = toInt(buf, 8);
                frameIndex.add(new Frame(fpos,len));
                byte[] bufData = new byte[len]; // The actual data that is to be drawn on the screen.           
                pos = 0;
                while (pos < len){
                    len = iStream.read(bufData, pos, len-pos);
                    pos = pos + len;
                    fpos+=len;
                }            
            }catch(Exception e){
            }
            //            String s = new String(drawData);
        
        }
    }

    public int loadFrame(int no, boolean bp){
        try{
            if (no>=frameIndex.size()){                
                no--;
                playThread.halt();
                return -1;        
            }    
            Frame frame = (Frame)frameIndex.get(no);            
            System.out.println("Attempting to draw frame number "+no+" Current frame is "+currentFrame);
//            if (no<currentFrame){
                reset();
                iStream.skip(frame.getPos());                
  //          } else {
//                 Frame temp = (Frame)frameIndex.get(currentFrame);                       
//                 int diff = frame.getPos()-temp.getPos();
//                 System.out.println("Diff is "+diff);                
//                 iStream.skip(diff);
//            }
            int len = frame.getLen();
            byte[] drawData = new byte[len]; // The actual data that is to be drawn on the screen.           
            int pos = 0;
            while (pos < len){
                len = iStream.read(drawData, pos, len-pos);
                pos = pos + len;
            }
            System.out.println();            
            if (bp){
                for (int i = 0; i<drawData.length; i++)
                    System.out.print(drawData[i]+" ");
                System.out.println();
            }
            
            drawThread.insertByteArray(drawData);
            drawThread.next();
        }catch(Exception e){
            e.printStackTrace();
            return -1;
        }
        return 0;
    }

    private int toInt(byte b[], int i){
        int  n = 0;
        int  f = 1;
        for (int k = 0; k < 4; k++){
            n = n + f * bconv(b[i+k]);
            f = f * 0x100;
        }
        return n;
        
    }
    
    private int bconv(byte b){
        if (b < 0)
            return b + 256;
        return b;
    }

    class DrawThread extends Thread{
        
        Terminal terminal;
        int bufferSize = 1000; // Default? (not yet implemented).
        int sleepLen, currentFrame = 0;
        boolean exitFlag = false, running = false;
        LinkedList queue = new LinkedList();

        public DrawThread(Terminal terminal, int sleepLen){
            this.sleepLen=sleepLen;
            this.terminal=terminal;
        }

        public DrawThread(Terminal terminal, int bufferSize, int sleepLen){
            this.sleepLen=sleepLen;
            this.terminal=terminal;
            this.bufferSize=bufferSize;
        }

        /* Halt because stop is taken by a depricated thread api :/ */
        public void halt(){ running=false; }
        
        public void begin(){ running=true; }
        
        public void exit(){ exitFlag=true; }
        
        public void insertString(String s){ queue.add(s); }

        public boolean hasCapacity(){
            return queue.size()<=bufferSize;
        }

        private void readFrame(){
            
        }

        public void clearScreen(){
            //ESC [2J 	 Clear entire screen
            byte clrscr[] = {0x1b,0x5b,0x32,0x4a};
            terminal.putString(new String(clrscr));
        }
        
        public void insertByteArray(byte[] a){
            // Replaces all instances of the 126 character (that causes an 
            // display bug due to insufficient font compatibility) with a
            // a character that is supported. Optional future replacements
            // can be done in the same loop.
            byte b[] = {0x5b,0x32,0x4a};
            int x = 0;
            for ( int i = 0; i<a.length; i++){
                if (a[i]==b[x]) {
                    if (x==b.length){
                        System.out.println("Clear screen");                    
                        x=0;
                    }
                } else x = 0;
                if (a[i]==126) a[i]=46;
            }            
            String s = new String(a);
            System.out.println("Size of frame: "+s.length());            
            queue.add(s);
            
        }

        public void next(){
            if (queue.size()>0){
                terminal.putString((String)queue.removeFirst());                
            } else
                System.out.println("Error, no frame in buffer!");
        }

        public void setSleep(int sleepLen){
            this.sleepLen=sleepLen;
        }

        public void run(){            
            while(!exitFlag){
                if (running && queue.size()>0){
                    terminal.putString((String)queue.removeFirst());
                    try{
                        sleep(sleepLen);
                    }catch(Exception e){
                    }
                } else {
                    try{
                        sleep(100);
                        yield();                
                    }catch(InterruptedException e){
                        System.out.println("Error, thread interrupted.");                        
                        e.printStackTrace();
                    }
                }
            }
        }
    }   

    class PlayThread extends Thread{
        
        boolean running = false;
        AppletPlayer player;
        int frame = 0;
        int sleep = 10;

        public PlayThread(AppletPlayer player){
            this.player = player;
        }

        public PlayThread(AppletPlayer player, int sleep){
            this.player = player;
            setSleep(sleep);
        }

        public void setSleep(int s){
            this.sleep=s;
        }
        
        /* Halt because stop is taken by a depricated thread api :/ */
        public int halt(){ running=false; return frame; }
        
        public void begin(){ running=true; }
        public void begin(int frame){ running=true; this.frame=frame; }

        public void run(){
            while(true){
                if (running){
                    player.loadFrame(frame++,false);
                    try{
                        sleep(sleep);
                    }catch(InterruptedException e){
                        System.out.println("Error, thread interrupted.");
                        e.printStackTrace();
                    }
                } else{
                    try{
                        sleep(100);
                        yield();                
                    }catch(InterruptedException e){
                        System.out.println("Error, thread interrupted.");                        
                        e.printStackTrace();
                    }
                }
                //                    player.nextFrame();
            }
        }
    }

    /*
      Wrapper for frame information in the frame index. A frame has a 
      position in the input stream and length.
    */
    class Frame{
        int pos, len;

        public Frame(int pos, int len){
            this.pos = pos;
            this.len = len;
        }
        
        public int getPos(){
            return pos;
        }

        public int getLen(){
            return len;
        }
    }
}
