const searchInput = document.getElementById('search');
const slangList = document.getElementById('slang-list');
const slangItems = slangList.getElementsByClassName('slang-item');

searchInput.addEventListener('input', () => {
  const filter = searchInput.value.toUpperCase();
  for (let i = 0; i < slangItems.length; i++) {
    const h2 = slangItems[i].getElementsByTagName('h2')[0];
    if (h2.textContent.toUpperCase().indexOf(filter) > -1) {
      slangItems[i].style.display = "";
    } else {
      slangItems[i].style.display = "none";
    }
  }
});
