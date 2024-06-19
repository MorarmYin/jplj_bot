document.getElementById('toggleViewBtn').addEventListener('click', function () {
    var tableView = document.getElementById('tableView');
    var waterfallView = document.getElementById('waterfallView');
    if (tableView.style.display === 'none') {
        tableView.style.display = 'block';
        waterfallView.style.display = 'none';
    } else {
        tableView.style.display = 'none';
        waterfallView.style.display = 'block';
    }
});