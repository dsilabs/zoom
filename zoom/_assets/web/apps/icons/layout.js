
const searchBox = document.getElementById('searchBox');
const icons = document.querySelectorAll(".icon-item");
const copiedMessage = document.getElementById('copied-message');
var delayTimer;
var messageDelayTimer;

function hideIcon(icon){
  icon.classList.add("hidden-icon");
}

function showIcon(icon){
  icon.classList.remove("hidden-icon");
}

function filterIcon(icon) {
  var visible;

  description = icon.className.replace('icon-item ', '');

  visible = false;
  if ( description.includes(searchText) ){
    visible = true;
    console.log(description);
  }

  if (visible) {
    showIcon(icon)
  } else {
    hideIcon(icon)
  }
}

function filterIconsInner() {
  searchText = searchBox.value.toLowerCase();

  console.log(searchText);
  icons.forEach(icon => filterIcon(icon));

  searchBox.focus();
  searchBox.select();
}

function filterIcons() {
  clearTimeout(delayTimer);
  delayTimer = setTimeout(filterIconsInner, 1000);
}

function removeMessage(){
  copiedMessage.classList.remove('copied-message-visible')
}

function clickIcon(icon) {
  navigator.clipboard.writeText(icon.target.title);
  copiedMessage.classList.add('copied-message-visible')
  clearTimeout(messageDelayTimer);
  messageDelayTimer = setTimeout(removeMessage, 1000);
}

searchBox.addEventListener("keyup", filterIcons);
icons.forEach(icon => icon.addEventListener('click', clickIcon))
