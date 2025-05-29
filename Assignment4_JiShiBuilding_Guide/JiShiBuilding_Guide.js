let JishiRooms = [];

// 加载 JSON 数据
fetch('./rooms.json')
    .then(response => response.json())
    .then(data => {
        JishiRooms = data.rooms;
        updateUI(currentImage); // 初始化 UI
    })
    .catch(error => {
        console.error('Error loading rooms.json:', error);
        const container = document.querySelector('.image-container');
        container.innerHTML = `<p style="color: red; text-align: center;">Failed to load room data 😭</p>`;
    });

// 这里存储着显示的三张图片的位置：左边，中间和右边
const imageOrder = [
    { imageLocation: 'left' },
    { imageLocation: 'middle' },
    { imageLocation: 'right' }
];

// 当前图片：软件学院招牌401
let currentImage = 33;
// 找到页面预留的图片容器
const container = document.querySelector('.image-container');

// 左箭头
const leftArrow = document.createElement('div');
leftArrow.innerHTML = `🢀`;
leftArrow.classList.add("left-arrow");
leftArrow.style = "display: flex; flex-direction: column; justify-content: center; cursor: pointer; font-size: 40px;";
leftArrow.addEventListener('click', leftPressed);

// 右箭头
const rightArrow = document.createElement('div');
rightArrow.innerHTML = `🢂`;
rightArrow.classList.add("right-arrow");
rightArrow.style = "display: flex; flex-direction: column; justify-content: center; cursor: pointer; font-size: 40px;";
rightArrow.addEventListener('click', rightPressed);

// 搜索内容的找到和绑定
const search = document.getElementById('search-content');
search.addEventListener('keyup', searchRooms);

// 按键快捷键的找到和绑定
const collectionButton = document.getElementsByClassName("clickbutton");
for (let i = 0; i < collectionButton.length; i++) {
    collectionButton[i].addEventListener('click', () => { buttonPressed(i); });
}

// 按键快捷键绑定的函数
function buttonPressed(i) {
    container.innerHTML = "";
    currentImage = (i - 1 + JishiRooms.length) % JishiRooms.length;
    updateUI(currentImage);
}

// 左箭头按键绑定的函数
function leftPressed() {
    container.innerHTML = "";
    currentImage = (currentImage + JishiRooms.length - 1) % JishiRooms.length;
    updateUI(currentImage);
}

// 右箭头按键绑定的函数
function rightPressed() {
    container.innerHTML = "";
    currentImage = (currentImage + 1) % JishiRooms.length;
    updateUI(currentImage);
}

// 以currentImage为传入参数更新container中的图片显示UI
function updateUI(currentImage) {
    container.innerHTML = "";
    container.classList.remove('search-results');
    container.appendChild(leftArrow);

    imageOrder.forEach((data, index) => {
        const panel = document.createElement('div');
        panel.classList.add('panel', data.imageLocation);

        const roomIndex = (currentImage + index) % JishiRooms.length;
        const room = JishiRooms[roomIndex];

        panel.style.backgroundImage = room.image;
        panel.innerHTML = `
            <h3 style="font-family: 'Times New Roman'; margin-top: 420px; opacity: 1; text-align: center; font-size: 36px;">${room.number}</h3>
            <p style="font-family: 'Times New Roman'; margin-top: 60px; opacity: 1; text-align: center; font-size: 18px; color : black">${room.descriptions}</p>`;

        container.appendChild(panel);
    });

    container.appendChild(rightArrow);
}

// 简单子字符串匹配得分
function partialRatio(str1, str2) {
    str1 = str1.toLowerCase();
    str2 = str2.toLowerCase();
    if (!str1 || !str2) return 0;

    let maxScore = 0;
    const shorter = str1.length < str2.length ? str1 : str2;
    const longer = str1.length < str2.length ? str2 : str1;

    for (let i = 0; i <= longer.length - shorter.length; i++) {
        const substring = longer.slice(i, i + shorter.length);
        let matchCount = 0;
        for (let j = 0; j < shorter.length; j++) {
            if (substring[j] === shorter[j]) matchCount++;
        }
        const score = (matchCount / shorter.length) * 100;
        maxScore = Math.max(maxScore, score);
    }
    return Math.round(maxScore);
}

// 关键词搜索函数
function searchRooms() {
    container.innerHTML = "";
    container.classList.add('search-results');

    if (search.value && search.value.trim() !== "") {
        const searchValue = search.value.trim();
        const queries = searchValue.toLowerCase().split(/\s+/);
        let matchedRooms = [];

        JishiRooms.forEach(room => {
            let scores = [];
            queries.forEach(q => {
                const nameScore = partialRatio(q, room.descriptions);
                const keywordScores = room.key_words.map(kw => partialRatio(q, kw));
                const maxKeywordScore = keywordScores.length ? Math.max(...keywordScores) : 0;
                const maxScore = Math.max(nameScore, maxKeywordScore);
                scores.push(maxScore);
            });
            const avgScore = scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
            if (avgScore >= 60) {
                matchedRooms.push({ room: room, score: Math.round(avgScore * 100) / 100 });
            }
        });

        matchedRooms.sort((a, b) => b.score - a.score);

        if (matchedRooms.length > 0) {
            matchedRooms.forEach(result => {
                const room = result.room;
                const panel = document.createElement('div');
                panel.classList.add('panel');
                panel.style.backgroundImage = room.image;
                panel.innerHTML = `
                    <h3 style="font-family: 'Times New Roman'; margin-top: 420px; opacity: 1; text-align: center; font-size: 36px;">${room.number}</h3>`;
                container.appendChild(panel);
            });
        } else {
            const panel = document.createElement('div');
            panel.classList.add('panel');
            panel.innerHTML = `<p style="opacity: 1; color: black; text-align: center; font-size: 35px; font-weight: bold;">啊哦!无搜索结果😭</p>`;
            container.appendChild(panel);
        }
    } else {
        updateUI(currentImage);
    }
}