using CommunityToolkit.Mvvm.Input;
using uzoncalc.Models;

namespace uzoncalc.PageModels
{
    public interface IProjectTaskPageModel
    {
        IAsyncRelayCommand<ProjectTask> NavigateToTaskCommand { get; }
        bool IsBusy { get; }
    }
}