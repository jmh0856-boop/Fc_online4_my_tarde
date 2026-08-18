const nicknameInput = document.getElementById("nickname");
const searchButton = document.getElementById("search-button");
const statusElement = document.getElementById("status");
const tradeList = document.getElementById("trade-list");
const pagination = document.getElementById("pagination");
const tabs = document.querySelectorAll(".trade-tab");

let currentOuid = null;
let currentTradeType = "all";
let currentPage = 1;

const pageSize = 10;


// ==============================
// 닉네임 조회
// ==============================

async function searchNickname() {

    const nickname = nicknameInput.value.trim();

    if (!nickname) {
        statusElement.textContent = "닉네임을 입력해주세요.";
        return;
    }

    statusElement.textContent = "선수 정보를 조회하는 중...";

    tradeList.innerHTML = "";
    pagination.innerHTML = "";

    try {

        const response = await fetch(
            `/users/lookup?nickname=${encodeURIComponent(nickname)}`
        );

        if (!response.ok) {
            throw new Error("닉네임을 찾을 수 없습니다.");
        }

        const data = await response.json();

        currentOuid = data.ouid;
        currentPage = 1;

        await loadTrades();

    } catch (error) {

        statusElement.textContent = error.message;

    }
}


// ==============================
// 거래내역 조회
// ==============================

async function loadTrades() {

    if (!currentOuid) {
        return;
    }

    statusElement.textContent = "거래내역을 불러오는 중...";
    tradeList.innerHTML = "";

    try {

        const url =
            `/trades/${currentOuid}` +
            `?tradetype=${currentTradeType}` +
            `&page=${currentPage}` +
            `&size=${pageSize}`;

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error("거래내역 조회에 실패했습니다.");
        }

        const data = await response.json();

        renderTrades(data);
        renderPagination(data);

        statusElement.textContent =
            `총 ${data.total}건의 거래내역`;

    } catch (error) {

        statusElement.textContent = error.message;

    }
}


// ==============================
// 거래 카드 생성
// ==============================

function createTradeCard(trade) {

    const isBuy = trade.trade_type === "buy";

    const tradeLabel = isBuy
        ? "🟢 구매"
        : "🔴 판매";

    const tradeClass = isBuy
        ? "buy"
        : "sell";

    const value = formatValue(trade.value);

    const date = formatDate(trade.trade_date);

    const card = document.createElement("article");

    card.className = "trade-card";

    card.innerHTML = `
        <div class="player-image-wrapper">

            <img
                class="player-image"
                src="${trade.player_img}"
                alt="${trade.player_name}"
                loading="lazy"
            >

        </div>

        <div class="trade-info">

            <div class="trade-type ${tradeClass}">
                ${tradeLabel}
            </div>

            <div class="player-name">
                ${trade.player_name}
            </div>

            <div class="season-info">
                ${getSeasonShortName(trade.season_name)} · +${trade.grade}
            </div>

            <div class="trade-date">
                ${date}
            </div>

        </div>

        <div class="trade-value">
            ${value}
        </div>
    `;

    return card;
}


// ==============================
// 거래내역 렌더링
// ==============================

function renderTrades(data) {

    tradeList.innerHTML = "";

    if (!data.items || data.items.length === 0) {

        tradeList.innerHTML =
            `<p class="empty-message">거래내역이 없습니다.</p>`;

        return;
    }

    for (const trade of data.items) {

        const card = createTradeCard(trade);

        tradeList.appendChild(card);
    }
}


// ==============================
// 시즌 이름
// ==============================

function getSeasonShortName(seasonName) {

    if (!seasonName) {
        return "";
    }

    // "25DP (25 Devoted Player)"
    // → "25DP"
    const match = seasonName.match(/^([^(]+)/);

    if (match) {
        return match[1].trim();
    }

    return seasonName;
}


// ==============================
// 금액 표시
// ==============================

function formatValue(value) {

    const trillion = 1_000_000_000_000;
    const billion = 100_000_000;
    const million = 10_000;

    if (value >= trillion) {

        return (
            (value / trillion)
                .toFixed(1)
                .replace(".0", "")
            + "조 BP"
        );
    }

    if (value >= billion) {

        return (
            (value / billion)
                .toFixed(1)
                .replace(".0", "")
            + "억 BP"
        );
    }

    if (value >= million) {

        return (
            (value / million)
                .toFixed(1)
                .replace(".0", "")
            + "만 BP"
        );
    }

    return value.toLocaleString("ko-KR") + " BP";
}


// ==============================
// 날짜 표시
// ==============================

function formatDate(dateString) {

    const date = new Date(`${dateString}Z`);

    return date.toLocaleString(
        "ko-KR",
        {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
        }
    );
}


// ==============================
// 페이지네이션
// ==============================

function renderPagination(data) {

    pagination.innerHTML = "";

    if (data.page > 1) {

        const previousButton =
            document.createElement("button");

        previousButton.textContent = "‹";

        previousButton.addEventListener(
            "click",
            () => {

                currentPage--;

                loadTrades();
            }
        );

        pagination.appendChild(previousButton);
    }


    const totalPages =
        Math.ceil(data.total / data.size);


    for (
        let page = 1;
        page <= totalPages;
        page++
    ) {

        const button =
            document.createElement("button");

        button.textContent = page;

        if (page === data.page) {

            button.classList.add("active");
        }

        button.addEventListener(
            "click",
            () => {

                currentPage = page;

                loadTrades();
            }
        );

        pagination.appendChild(button);
    }


    if (data.has_next) {

        const nextButton =
            document.createElement("button");

        nextButton.textContent = "›";

        nextButton.addEventListener(
            "click",
            () => {

                currentPage++;

                loadTrades();
            }
        );

        pagination.appendChild(nextButton);
    }
}


// ==============================
// 검색 버튼
// ==============================

searchButton.addEventListener(
    "click",
    searchNickname
);


// ==============================
// Enter 키
// ==============================

nicknameInput.addEventListener(
    "keydown",
    (event) => {

        if (event.key === "Enter") {

            searchNickname();
        }

    }
);


// ==============================
// 전체 / 구매 / 판매
// ==============================

tabs.forEach((tab) => {

    tab.addEventListener(
        "click",
        () => {

            tabs.forEach((item) => {

                item.classList.remove("active");
            });

            tab.classList.add("active");

            currentTradeType =
                tab.dataset.type;

            currentPage = 1;

            loadTrades();
        }
    );

});