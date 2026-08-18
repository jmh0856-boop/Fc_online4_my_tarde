const nicknameInput = document.getElementById("nickname");
const searchButton = document.getElementById("search-button");
const statusElement = document.getElementById("status");
const tradeList = document.getElementById("trade-list");
const pagination = document.getElementById("pagination");

const tabs = document.querySelectorAll(".trade-tab");

const startDateInput = document.getElementById("start-date");
const endDateInput = document.getElementById("end-date");
const dateSearchButton =
    document.getElementById("date-search-button");

const apiKeyInput = document.getElementById("api-key");
const saveApiKeyButton =
    document.getElementById("save-api-key-button");

const apiKeyStatus =
    document.getElementById("api-key-status");


let currentOuid = null;
let currentTradeType = "all";
let currentPage = 1;

const pageSize = 10;


// =====================================================
// API KEY
// =====================================================

function getApiKey() {

    return apiKeyInput.value.trim();
}


function validateApiKey() {

    const apiKey = getApiKey();

    if (!apiKey) {

        apiKeyStatus.textContent =
            "API Key를 입력해주세요.";

        apiKeyStatus.className =
            "api-key-status error";

        return false;
    }

    return true;
}


saveApiKeyButton.addEventListener(
    "click",
    () => {

        const apiKey = getApiKey();

        if (!apiKey) {

            apiKeyStatus.textContent =
                "API Key를 입력해주세요.";

            apiKeyStatus.className =
                "api-key-status error";

            return;
        }

        apiKeyStatus.textContent =
            "API Key가 입력되었습니다.";

        apiKeyStatus.className =
            "api-key-status success";

        statusElement.textContent =
            "API Key가 준비되었습니다.";
    }
);


// =====================================================
// 공통 API Header
// =====================================================

function getApiHeaders() {

    const apiKey = getApiKey();

    return {
        "X-Nexon-Api-Key": apiKey,
        "Content-Type": "application/json",
    };
}


// =====================================================
// 닉네임 조회
// =====================================================

async function searchNickname() {

    if (!validateApiKey()) {
        return;
    }

    const nickname =
        nicknameInput.value.trim();

    if (!nickname) {

        statusElement.textContent =
            "닉네임을 입력해주세요.";

        return;
    }

    statusElement.textContent =
        "닉네임을 조회하는 중...";

    tradeList.innerHTML = "";
    pagination.innerHTML = "";

    try {

        const response = await fetch(
            `/users/${encodeURIComponent(nickname)}`,
            {
                method: "GET",
                headers: getApiHeaders(),
            }
        );

        if (!response.ok) {

            let message =
                "닉네임을 찾을 수 없습니다.";

            try {

                const errorData =
                    await response.json();

                if (errorData.detail) {
                    message = errorData.detail;
                }

            } catch (error) {
                // JSON 오류는 무시
            }

            throw new Error(message);
        }

        const data =
            await response.json();

        currentOuid = data.ouid;
        currentPage = 1;

        await loadTrades();

    } catch (error) {

        console.error(error);

        statusElement.textContent =
            error.message;
    }
}


// =====================================================
// 거래내역 조회
// =====================================================

async function loadTrades() {

    if (!currentOuid) {
        return;
    }

    if (!validateApiKey()) {
        return;
    }

    statusElement.textContent =
        "거래내역을 불러오는 중...";

    tradeList.innerHTML = "";
    pagination.innerHTML = "";

    try {

        const params =
            new URLSearchParams();

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


        // ---------------------------------------------
        // 시작일
        // ---------------------------------------------

        if (
            startDateInput &&
            startDateInput.value
        ) {

            params.append(
                "start_date",
                startDateInput.value
            );
        }


        // ---------------------------------------------
        // 종료일
        // ---------------------------------------------

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
            await fetch(
                url,
                {
                    method: "GET",
                    headers: getApiHeaders(),
                }
            );


        if (!response.ok) {

            let message =
                "거래내역 조회에 실패했습니다.";

            try {

                const errorData =
                    await response.json();

                if (errorData.detail) {
                    message = errorData.detail;
                }

            } catch (error) {
                // JSON 오류는 무시
            }

            throw new Error(message);
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


// =====================================================
// 거래 카드
// =====================================================

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

        <div class="player-card">

            <img
                class="card-season"
                src="${trade.season_img}"
                alt="${trade.season_name}"
                loading="lazy"
            >

            <img
                class="card-player"
                src="${trade.player_img}"
                alt="${trade.player_name}"
                loading="lazy"
            >

            <div class="card-grade">
                +${trade.grade}
            </div>

            <div class="card-player-name">
                ${trade.player_name}
            </div>

        </div>


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


        <div class="trade-value">
            ${value}
        </div>

    `;


    return card;
}


// =====================================================
// 거래내역 렌더링
// =====================================================

function renderTrades(data) {

    tradeList.innerHTML = "";


    if (
        !data.items ||
        data.items.length === 0
    ) {

        tradeList.innerHTML =
            `<p class="empty-message">
                거래내역이 없습니다.
            </p>`;

        return;
    }


    for (const trade of data.items) {

        const card =
            createTradeCard(trade);

        tradeList.appendChild(card);
    }
}


// =====================================================
// 시즌 이름
// =====================================================

function getSeasonShortName(
    seasonName
) {

    if (!seasonName) {
        return "";
    }


    const match =
        seasonName.match(/^([^(]+)/);


    if (match) {

        return match[1].trim();
    }


    return seasonName;
}


// =====================================================
// 금액
// =====================================================

function formatValue(value) {

    const trillion =
        1_000_000_000_000;

    const billion =
        100_000_000;

    const million =
        10_000;


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


    return (
        value.toLocaleString("ko-KR")
        + " BP"
    );
}


// =====================================================
// 날짜
// =====================================================

function formatDate(
    dateString
) {

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


// =====================================================
// 페이지네이션
// =====================================================

function renderPagination(data) {

    pagination.innerHTML = "";


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


        if (page === data.page) {

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


// =====================================================
// 닉네임 조회 버튼
// =====================================================

searchButton.addEventListener(
    "click",
    searchNickname
);


// =====================================================
// 닉네임 Enter
// =====================================================

nicknameInput.addEventListener(
    "keydown",
    (event) => {

        if (event.key === "Enter") {

            searchNickname();
        }
    }
);


// =====================================================
// API Key Enter
// =====================================================

apiKeyInput.addEventListener(
    "keydown",
    (event) => {

        if (event.key === "Enter") {

            saveApiKeyButton.click();
        }
    }
);


// =====================================================
// 거래 탭
// =====================================================

tabs.forEach(
    (tab) => {

        tab.addEventListener(
            "click",
            () => {

                tabs.forEach(
                    (item) => {

                        item.classList.remove(
                            "active"
                        );
                    }
                );


                tab.classList.add(
                    "active"
                );


                currentTradeType =
                    tab.dataset.type;


                currentPage = 1;


                if (currentOuid) {

                    loadTrades();
                }
            }
        );
    }
);


// =====================================================
// 기간 조회
// =====================================================

if (dateSearchButton) {

    dateSearchButton.addEventListener(
        "click",
        () => {

            const startDate =
                startDateInput.value;

            const endDate =
                endDateInput.value;


            if (
                startDate &&
                endDate &&
                startDate > endDate
            ) {

                statusElement.textContent =
                    "시작일은 종료일보다 늦을 수 없습니다.";

                return;
            }


            if (!currentOuid) {

                statusElement.textContent =
                    "먼저 닉네임을 조회해주세요.";

                return;
            }


            currentPage = 1;

            loadTrades();
        }
    );
}