let tg = window.Telegram.WebApp;
tg.expand(); //расширяем на все окно

tg.MainButton.text = "Changed Text"; //изменяем текст кнопки
tg.MainButton.setText("Changed Text1"); //изменяем текст кнопки иначе
tg.MainButton.textColor = "#F55353"; //изменяем цвет текста кнопки
tg.MainButton.color = "#143F6B"; //изменяем цвет бэкграунда кнопки
tg.MainButton.hide(); //скрываем кнопку





let btn = document.getElementById("btn"); //получаем кнопку скрыть/показать
btn.addEventListener('click', function(){ //вешаем событие на нажатие html-кнопки
   if (tg.MainButton.isVisible){ //если кнопка показана
      tg.MainButton.hide() //скрываем кнопку
   }
   else{ //иначе
      tg.MainButton.show() //показываем
   }
});

let btnED = document.getElementById("btnED"); //получаем кнопку активировать/деактивировать
btnED.addEventListener('click', function(){ //вешаем событие на нажатие html-кнопки
   if (tg.MainButton.isActive){ //если кнопка показана
      tg.MainButton.setParams({"color": "#E0FFFF"}); //меняем цвет
      tg.MainButton.disable() //скрываем кнопку
   }
   else{ //иначе
      tg.MainButton.setParams({"color": "#143F6B"}); //меняем цвет
      tg.MainButton.enable() //показываем
   }
});

Telegram.WebApp.onEvent('mainButtonClicked', function(){
   tg.sendData("some string that we need to send");
   //при клике на основную кнопку отправляем данные в строковом виде
});



let i = 2;
function updater() {

  let text = document.getElementById("deals");
  text.textContent = "timer " + i;
  i++;
 }

setInterval(updater, 1000);
//alert('data: ' + document.URL.search('bitrix_id'))
alert(tg.initData);
 //updater()
//работает только в attachment menu
// let pic = document.createElement('img'); //создаем img
// pic.src = tg.initDataUnsafe.user.photo_url; //задаём src
// usercard.appendChild(pic); //добавляем элемент в карточку