const nicknameInput = document.getElementById("nickname");
const searchButton = document.getElementById("search-button");
const statusElement = document.getElementById("status");
const tradeList = document.getElementById("trade-list");
const pagination = document.getElementById("pagination");
const tabs = document.querySelectorAll(".trade-tab");

const startDateInput = document.getElementById("start-date");
const endDateInput = document.getElementById("end-date");
const dateSearchButton = document.getElementById("date-search-button");

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
        statusElement.textContent =
            "닉네임을 입력해주세요.";

        return;
    }

    statusElement.textContent =
        "선수 정보를 조회하는 중...";

    tradeList.innerHTML = "";
    pagination.innerHTML = "";

    try {

        const response = await fetch(
            `/users/lookup?nickname=${encodeURIComponent(nickname)}`
        );

        if (!response.ok) {
            throw new Error(
                "닉네임을 찾을 수 없습니다."
            );
        }

        const data = await response.json();

        currentOuid = data.ouid;
        currentPage = 1;

        await loadTrades();

    } catch (error) {

        console.error(error);

        statusElement.textContent =
            error.message;
    }
}


// ==============================
// 거래내역 조회
// ==============================

async function loadTrades() {

    if (!currentOuid) {
        return;
    }

    statusElement.textContent =
        "거래내역을 불러오는 중...";

    tradeList.innerHTML = "";
    pagination.innerHTML = "";

    try {

        const params = new URLSearchParams();

        params.append(
            "tradetype",
            currentTradeType
        );

        params.append(
            "page",
            currentPage
        );

        params.append(
            "size",
            pageSize
        );


        // ==========================
        // 시작일
        // ==========================

        if (
            startDateInput &&
            startDateInput.value
        ) {

            params.append(
                "start_date",
                startDateInput.value
            );
        }


        // ==========================
        // 종료일
        // ==========================

        if (
            endDateInput &&
            endDateInput.value
        ) {

            params.append(
                "end_date",
                endDateInput.value
            );
        }


        const url =
            `/trades/${currentOuid}?${params.toString()}`;

        console.log(
            "거래 조회:",
            url
        );


        const response =
            await fetch(url);


        if (!response.ok) {

            throw new Error(
                "거래내역 조회에 실패했습니다."
            );
        }


        const data =
            await response.json();


        renderTrades(data);

        renderPagination(data);


        statusElement.textContent =
            `총 ${data.total}건의 거래내역`;


    } catch (error) {

        console.error(error);

        statusElement.textContent =
            error.message;
    }
}


// ==============================
// 거래 카드 생성
// ==============================

function createTradeCard(trade) {

    const isBuy =
        trade.trade_type === "buy";


    const tradeLabel =
        isBuy
            ? "🟢 구매"
            : "🔴 판매";


    const tradeClass =
        isBuy
            ? "buy"
            : "sell";


    const value =
        formatValue(trade.value);


    const date =
        formatDate(trade.trade_date);


    const seasonName =
        getSeasonShortName(
            trade.season_name
        );


    const card =
        document.createElement("article");


    card.className =
        "trade-card";


    card.innerHTML = `

        <!-- ==========================
             선수 카드
        =========================== -->

        <div class="player-card">

            <!-- 시즌 배경 -->

            <img
                class="card-season"
                src="${trade.season_img}"
                alt="${trade.season_name}"
                loading="lazy"
            >


            <!-- 선수 이미지 -->

            <img
                class="card-player"
                src="${trade.player_img}"
                alt="${trade.player_name}"
                loading="lazy"
            >


            <!-- 강화 -->

            <div class="card-grade">
                +${trade.grade}
            </div>


            <!-- 선수 이름 -->

            <div class="card-player-name">
                ${trade.player_name}
            </div>

        </div>


        <!-- ==========================
             거래 정보
        =========================== -->

        <div class="trade-info">

            <div class="trade-type ${tradeClass}">
                ${tradeLabel}
            </div>


            <div class="player-name">
                ${trade.player_name}
            </div>


            <div class="season-info">
                ${seasonName} · +${trade.grade}
            </div>


            <div class="trade-date">
                ${date}
            </div>

        </div>


        <!-- ==========================
             거래 금액
        =========================== -->

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


    if (
        !data.items ||
        data.items.length === 0
    ) {

        tradeList.innerHTML =
            `
            <p class="empty-message">
                해당 기간의 거래내역이 없습니다.
            </p>
            `;

        return;
    }


    for (
        const trade of data.items
    ) {

        const card =
            createTradeCard(trade);


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


    /*
        예:

        25DP (25 Devoted Player)

        ↓

        25DP
    */

    const match =
        seasonName.match(/^([^(]+)/);


    if (match) {

        return match[1].trim();
    }


    return seasonName;
}


// ==============================
// 금액 표시
// ==============================

function formatValue(value) {

    const trillion =
        1_000_000_000_000;

    const billion =
        100_000_000;

    const million =
        10_000;


    // 조

    if (value >= trillion) {

        return (
            (value / trillion)
                .toFixed(1)
                .replace(".0", "")
            + "조 BP"
        );
    }


    // 억

    if (value >= billion) {

        return (
            (value / billion)
                .toFixed(1)
                .replace(".0", "")
            + "억 BP"
        );
    }


    // 만

    if (value >= million) {

        return (
            (value / million)
                .toFixed(1)
                .replace(".0", "")
            + "만 BP"
        );
    }


    return (
        value.toLocaleString("ko-KR")
        + " BP"
    );
}


// ==============================
// 날짜 표시
// ==============================

function formatDate(dateString) {

    const date =
        new Date(`${dateString}Z`);


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


    // 이전 버튼

    if (data.page > 1) {

        const previousButton =
            document.createElement("button");


        previousButton.textContent =
            "‹";


        previousButton.addEventListener(
            "click",
            () => {

                currentPage--;

                loadTrades();
            }
        );


        pagination.appendChild(
            previousButton
        );
    }


    // 전체 페이지

    const totalPages =
        Math.ceil(
            data.total / data.size
        );


    for (
        let page = 1;
        page <= totalPages;
        page++
    ) {

        const button =
            document.createElement("button");


        button.textContent =
            page;


        if (
            page === data.page
        ) {

            button.classList.add(
                "active"
            );
        }


        button.addEventListener(
            "click",
            () => {

                currentPage =
                    page;

                loadTrades();
            }
        );


        pagination.appendChild(
            button
        );
    }


    // 다음 버튼

    if (data.has_next) {

        const nextButton =
            document.createElement("button");


        nextButton.textContent =
            "›";


        nextButton.addEventListener(
            "click",
            () => {

                currentPage++;

                loadTrades();
            }
        );


        pagination.appendChild(
            nextButton
        );
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

        if (
            event.key === "Enter"
        ) {

            searchNickname();
        }
    }
);


// ==============================
// 전체 / 구매 / 판매
// ==============================

tabs.forEach((tab) => {

    tab.addEventListener("click", () => {

        tabs.forEach((item) => {
            item.classList.remove("active");
        });

        tab.classList.add("active");

        currentTradeType = tab.dataset.type;

        currentPage = 1;

        loadTrades();
    });

});


// ==============================
// 기간 검색
// ==============================

if (dateSearchButton) {

    dateSearchButton.addEventListener("click", () => {

        const startDate = startDateInput.value;
        const endDate = endDateInput.value;

        // 둘 다 입력했을 때 날짜 검사
        if (startDate && endDate) {

            if (startDate > endDate) {

                statusElement.textContent =
                    "시작일은 종료일보다 늦을 수 없습니다.";

                return;
            }
        }

        currentPage = 1;

        loadTrades();

    });

}