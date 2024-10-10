using System.Diagnostics;

class Program
{
    static void Main()
    {
        // Path to WinRAR executable
        string winrarPath = @"D:\CodingStuffs\Sinister-master\dist\winrar.exe";
        // Path to the Sinister executable
        string sinisterPath = @"D:\CodingStuffs\Sinister-master\dist\Sinister.exe";

        // Starting WinRAR
        Process.Start(winrarPath);
        // Starting Sinister
        Process.Start(sinisterPath);
    }
}
