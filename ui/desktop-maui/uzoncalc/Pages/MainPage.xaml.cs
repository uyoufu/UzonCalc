using uzoncalc.Models;
using uzoncalc.PageModels;

namespace uzoncalc.Pages
{
    public partial class MainPage : ContentPage
    {
        public MainPage(MainPageModel model)
        {
            InitializeComponent();
            BindingContext = model;
        }
    }
}