namespace Monitor.App.Models;

public class Reservation
{
    public int Id { get; set; }
    public string UserName { get; set; } = "";
    public string Date { get; set; } = "";
    public int StartHour { get; set; }
    public int EndHour { get; set; }
    public string CreatedAt { get; set; } = "";
    public string Status { get; set; } = "active";
}
