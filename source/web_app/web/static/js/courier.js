let tg = window.Telegram.WebApp;

tg.expand(); //��������� �� ��� ����

tg.MainButton.text = "Changed Text"; //�������� ����� ������
tg.MainButton.setText("Changed Text1"); //�������� ����� ������ �����
tg.MainButton.textColor = "#F55353"; //�������� ���� ������ ������
tg.MainButton.color = "#143F6B"; //�������� ���� ���������� ������
tg.MainButton.setParams({"color": "#143F6B"}); //��� ���������� ��� ���������
tg.MainButton.hide();
const telegram_id = (new URL(document.URL)).pathname.split("/")[3];


// � �������� �������
let btn_today = document.getElementById("btn_today");
btn_today.addEventListener('click', function(){
    btn_today.disabled = false;
    btn_tomorrow.disabled = true;
    btn_early.disabled = true;

    generator_deals_div("today");
});

// � �������� ������
let btn_tomorrow = document.getElementById("btn_tomorrow");
btn_tomorrow.addEventListener('click', function(){
    btn_today.disabled = true;
    btn_tomorrow.disabled = false;
    btn_early.disabled = true;

    generator_deals_div("tomorrow");
});


// ����������� �������
let btn_early = document.getElementById("btn_early");
btn_early.addEventListener('click', function(){
    btn_today.disabled = true;
    btn_tomorrow.disabled = true;
    btn_early.disabled = false;

    generator_deals_div("early");
});


function finish_deal(type, deal_id) {
    let param_tg = "telegram_id=" + telegram_id;
    let param_token = "token=jksSAsdf3jm3NDS88ccV"; // TODO: ������� ����� � ���������� ���������� ������ �� ����������
    let param_deal_id = "deal_id=" + deal_id;
    let xhr = new XMLHttpRequest();
    if (type === "done"){
        xhr.open("GET", "https://msopalev.ru:30300/api/v1/courier/deal/done?" +
            param_tg +"&"+param_token+"&"+param_deal_id, false);
    } else if (type === "return") {
        xhr.open("GET", "https://msopalev.ru:30300/api/v1/courier/deal/return?" +
            param_tg +"&"+param_token+"&"+param_deal_id, false);
    }
    xhr.send();
    xhr.onload = function() {
        if (xhr.status !== 200) {
            console.log('err', xhr.responseText);
            alert("��������� ������, ���������� �����!");
        }
    }
    return xhr.status;
}


// ����� ���������
function deal_done(deal_id){
    let deal = document.getElementById(deal_id);
    console.log(deal)
    //deal.classList.add('.animate-del');
    //deal.style.animation = "3s linear 1s infinite running slidein";

    let text = document.createElement('p');
    deal.append(text)

    deal.classList.toggle("hidden");
    setTimeout(() => {deal.remove();}, 1000);
}

// ����� ��������� �� �����
function deal_return(deal_id){
    finish_deal("return", deal_id);
    // TODO: �������� ��������
}


function get_deals(method){
    let xhr = new XMLHttpRequest();
    if (method === "today"){
        xhr.open("GET", "https://msopalev.ru:30300/api/v1/courier/deals_today?" +
            "token=jksSAsdf3jm3NDS88ccV&telegram_id=" + telegram_id, false);
    } else if (method === "tomorrow") {
        xhr.open("GET", "https://msopalev.ru:30300/api/v1/courier/deals_tomorrow?" +
            "token=jksSAsdf3jm3NDS88ccV&telegram_id=" + telegram_id, false);
    } else if (method === "early") {
        xhr.open("GET", "https://msopalev.ru:30300/api/v1/courier/deals_early?" +
            "token=jksSAsdf3jm3NDS88ccV&telegram_id=" + telegram_id, false);
    }
    xhr.send();
    xhr.onload = function() {
        if (xhr.status !== 200) {
            console.log('err', xhr.responseText);
            alert("��������� ������, ���������� �����!");
        }
    }
    return JSON.parse(xhr.responseText);
}


// ��������� ����� ������
function generator_deals_div(deal_type) {
    let deals = get_deals(deal_type);
    let deals_block = document.getElementById("deals");
    deals_block.innerHTML = "";
    console.log('get_deals', deals);
    for (const iter in deals['result']) {
        let deal = deals['result'][iter]
        console.log("create deal", deal)
        let div = document.createElement('div');
        let btn_done = document.createElement('button');
        let btn_return = document.createElement('button');
        let text = document.createElement('p');
        let div_buttons = document.createElement('div');

        text.innerText = deal["text"];

        // ��������� "�������� ���������"
        btn_done.textContent = "��������\n���������";
        btn_done.className = "btn_deal";
        btn_done.addEventListener('click', () => { deal_done(deal['ID']); });

        // ��������� "��������� �� �����"
        btn_return.textContent = "��������\n�� �����";
        btn_return.className = "btn_deal";
        btn_return.addEventListener('click', () => { deal_return(deal['ID']); });

        div.id = deal['ID'];
        div.className = "deal";

        div_buttons.className = "deal_buttons";

        div.append(text);
        div_buttons.append(btn_done);
        div_buttons.append(btn_return);
        div.append(div_buttons);


        deals_block.append(div);
        // document.body.append(div);
    }
}


generator_deals_div("today");

// ��������� ������ ������
let diagonal = Math.sqrt(Math.pow(screen.height, 2) + Math.pow(screen.width, 2));
let rec_diag = 1000;
let rec_font = 30;
let font_size = rec_font / (diagonal / rec_diag);
document.body.style.fontSize = font_size.toString() + "px";


//console.log("send request")
//let res = get_deals("today");
//console.log(res['result'])