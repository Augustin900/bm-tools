/*
RDG - Random Delay Generator

Made by: HRK-EXEX and improved by 0xsys

Description:
- It generates a random delay SFZ file by creating a specified ammount of group sections with lorand, highrand to elliminate the absolute resonation frequency on chopped notes
*/




















#define _CRT_SECURE_NO_WARNINGS

#include <cmath>
#include <string>
#include <iostream>
#include <sstream>
#include <string.h>
#include <stdio.h>
#include <errno.h>

#if defined(_WIN32) || defined(_WIN64)
  #include <Windows.h>
#endif

#ifdef __linux__
  #include <termios.h>
  #include <unistd.h>
#endif
#include <sys/stat.h>

#if defined(_MSC_VER)
  #pragma comment(lib, "winmm.lib")
#endif

#define buf 1024
#define def_range 16384

FILE* Load;
FILE* Save;
FILE* LoadB;
FILE* include;
struct stat Fdat;

using namespace std;


#ifdef __linux__
char GetKey()
{
  struct termios oldt, newt;
  char ch;

  // Disable canonical mode and echo
  tcgetattr(STDIN_FILENO, &oldt);
  newt = oldt;
  newt.c_lflag &= ~(ICANON | ECHO);
  tcsetattr(STDIN_FILENO, TCSANOW, &newt);

  // Read one character
  read(STDIN_FILENO, &ch, 1);

  // Restore terminal
  tcsetattr(STDIN_FILENO, TCSANOW, &oldt);
  return ch;
}
#endif

void ClearConsole()
{
#if defined(_WIN32) || defined(_WIN64)
  HANDLE hConsole = GetStdHandle(STD_OUTPUT_HANDLE);
  if(hConsole == INVALID_HANDLE_VALUE)
    return;

  CONSOLE_SCREEN_BUFFER_INFO csbi;
  DWORD cellsWritten;
  DWORD consoleSize;

  // Get the number of character cells in the current buffer
  if(!GetConsoleScreenBufferInfo(hConsole, &csbi))
    return;
    
  consoleSize = csbi.dwSize.X * csbi.dwSize.Y;

  // Fill the entire screen with spaces
  FillConsoleOutputCharacter(hConsole, ' ', consoleSize, (COORD){0, 0}, &cellsWritten);

  // Fill the entire screen with the current text attributes
  FillConsoleOutputAttribute(hConsole, csbi.wAttributes, consoleSize, (COORD){0, 0}, &cellsWritten);

  // Move the cursor to the top-left corner
  SetConsoleCursorPosition(hConsole, (COORD){0, 0});
#endif

#ifdef __linux__
  printf("\033[2J\033[H");
  fflush(stdout);
#endif
}


void setCursorPos(int x, int y)
{
#if defined(_WIN32) || defined(_WIN64)
  //カーソルの位置を取得
  HANDLE hCons = GetStdHandle(STD_OUTPUT_HANDLE);
  COORD pos;
  pos.X = x;
  pos.Y = y;
  SetConsoleCursorPosition(hCons, pos);
#endif

#ifdef __linux__
  printf("\033[%d;%dH", x, y);
  fflush(stdout);
#endif
}

void quit()
{
  printf("\nThis app will close to press Enter Key...");
#if defined(_WIN32) || defined(_WIN64)
  bool flag = 0;
  if(GetAsyncKeyState(VK_RETURN))
    flag = !flag;
    
  while(1)
  {
    if(GetAsyncKeyState(VK_RETURN) && !flag)
      break;
    else if(GetAsyncKeyState(VK_RETURN) == 0 && flag)
      flag = !flag;
  }
#endif

#ifdef __linux__
  char key;
  while(1)
  {
    key = GetKey();
  
    if(key == '\n')
    {
      break;
      exit(0);
    }
  }
#endif
}

int fopen_safe(FILE **fp, const char *filename, const char *mode)
{
  if(!fp)
    return EINVAL;
  *fp = fopen(filename, mode);
  return (*fp == NULL) ? errno : 0;
}

int main(int argc, char* argv[])
{
  //system("cls"); // I don't like this shit
  printf("Random Delay/Offset Generator v1.3.3\nMade by HRK.EXEX and 0xSYS\nIt will overwrite if the file same name output file.\n\nDO NOT RUN THIS PROGRAM IF YOU DRAGGED ALREADY PROCESSED FILE\n\n");
  if(argc < 2)
  { 
    printf("How to use: D&D Normal sfz Files.\nThis program doesn't support folder.\n");
    printf("            If they're too longer(more 16,384 characters),\nThis program made a file for use #include.");
  }
  else
  {
    int loop, offset;
    float lorand = 0, hirand = 0;
    char RD[60];
    char multi[] = "Files";
    if(argc == 2)
      multi[4] = '\0';
    
    printf("Dragged %d %s.\nWhat is resolusion of Random Delay? (Example:10) ", argc - 1, multi);
    
    //(void)scanf("%d", &loop); // Don't like that also
    std::cin >> loop;
    bool overload;
    string temp, temp3, temp4, temp5, temp6, result, path, path2;
  
    for(int i = 1; i < argc; ++i)
    {
      setCursorPos(0, 9); 
      overload = 0;
      
      if(argc != 2)
        printf("%s (%d/%d)              ", argv[i],i,argc-1);
      else
        printf("%s", argv[i]);
      
      int cnt, cnt2, cnt3;
      stat(argv[i],&Fdat);
      if (Fdat.st_size >= def_range)
        overload = 1;
        
      fopen_safe(&Load, argv[i], "r");
      if(Load != 0)
      {
        temp4 = "";
        temp5 = "";
        temp6 = "";
        string ipath = argv[i];
        int ay = ipath.find_last_of("\\");
        ipath = ipath.substr(0, ay + 1) + "set"; 
        for(int j = 0; j < loop; ++j)
        {
          temp3 = ""; cnt = 0; cnt2 = 0; cnt3 = 0;
          setCursorPos(0, 11);
          printf("Section %d", j + 1);
          bool del = 0;
          char tmp[buf];
          memset(tmp, 0, sizeof(tmp));
          fseek(Load, 0, SEEK_SET);
          while(fgets(tmp, buf, Load) != NULL)
          {
            temp = (string)tmp;
            int addg = temp.find("<group>");
            int addr = temp.find("<region>");
            if(j != 0 && addg != string::npos && !del)
            {
              del = 1;
              if(!overload)
                temp3 = "";
              else
                temp6 = "";
            }
            else
            {
              if(j==0 && addg == string::npos && !del && overload && !cnt2)
                temp6 += temp;
            }
              if(addg != string::npos)
              {
                lorand = (float)j / (float)loop;
                hirand = (float)(j + 1) / (float)loop;
                offset = j * 100.0 / (float)loop;
                string temp2 = temp.substr(7);
                
                if(log10(loop) < 1)
                  sprintf(RD, " lorand=%.3f hirand=%.3f offset=%d", lorand, hirand, offset);
                else if(log10(loop) < 2)
                  sprintf(RD, " lorand=%.4f hirand=%.4f offset=%d", lorand, hirand, offset);
                else if(log10(loop) < 3)
                  sprintf(RD, " lorand=%.5f hirand=%.5f offset=%d", lorand, hirand, offset);
                else if(log10(loop) < 4)
                  sprintf(RD, " lorand=%.6f hirand=%.6f offset=%d", lorand, hirand, offset);
                else
                {
                  printf("ERROR! Do not set resolution to 0～1."); 
                  quit();
                  return 1; 
                }
                if(!overload) temp = temp.substr(0, 7) + RD + temp2;
                else
                {
                  temp6 += temp.substr(0, 7) + RD + temp2 + "#include \"set\"\n\n";
                }
                ++cnt2;
              }
              if(addr != string::npos)
              {
                if(overload)
                {
                  if(cnt2<2 && !j)
                    temp5 += temp;
                }
                ++cnt3;
              }
              if(!overload)
                temp3 += temp;
              ++cnt;
          }
          if(!overload)
            temp4 += temp3 + "\n"; else temp4 += temp6; 
        }
        result = temp4;
          
          if(overload)
          {
            fopen_safe(&include, ipath.c_str(), "w");
            if(include != 0)
            {
              fprintf(include, "%s", temp5.c_str());
            }
            else
            {
              printf("ERROR! couldn't load the file. (Text)");
            }
          }
          
        path = argv[i]; path = path.substr(0, path.length() - 4);
        
        std::ostringstream out_path;
        out_path << path << " RD" << loop << ".sfz";
        if(argc != 2)
          std::cout << "Output Name (Last One): " << out_path.str() << std::endl;
        else
          std::cout << "Output Name: " << out_path.str() << std::endl;
        int err = fopen_safe(&Save, out_path.str().c_str(), "w+");
        if(!err)
        {
          fprintf(Save, "%s", result.c_str());
        }
        else
          printf("Failed.\nError Code is %d\n", err);
      }
      else
      {
        printf("ERROR! couldn't load the file. (Text)"); 
        quit(); 
        return 1;
      }
      fclose(Load);
    }
  }
  printf("\nFinished!\n");
  quit();
  return 0;
}