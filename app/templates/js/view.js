// templates/js/view.js

/**
 * 閲覧画面用 JavaScript
 * 在室状況の取得および全文一致検索を行う
 */

let allStatusData = []; // 取得した全データを保持

let currentSearch = { // 検索データを保持
    name: "",
    department: "",
    grade: "",
    role: "",
    room: ""
};

document.addEventListener("DOMContentLoaded", () => {
    // 初期表示（全件）
    loadStatusData();

    // 検索ボタン押下時の処理
    document.getElementById("search-button")
        .addEventListener("click", applySearch);

    // ★ 5秒ごとに自動更新
    setInterval(() => {
        loadStatusData(true);
    }, 5000);
});

/**
 * 在室状況データを API から取得する
 * @param {boolean} isAuto 自動更新かどうか
 */
function loadStatusData(isAuto = false) {
    fetch("/api/status_view")
        .then(response => response.json())
        .then(data => {
            if (data.result !== "ok") {
                throw new Error("API error");
            }

            allStatusData = data.records.sort((a, b) => a.id - b.id);

            // ★ 検索条件がある場合は再適用
            if (hasActiveSearch()) {
                applySearch(true);
            } else {
                renderTable(allStatusData);
                if (!isAuto) {
                    showMessage("すべての対応状況を表示しています");
                }
            }
        })
        .catch(() => {
            if (!isAuto) {
                showMessage("在室状況の取得に失敗しました", true);
            }
        });
}

/**
 * 検索条件を取得し、全文一致で絞り込みを行う
 * @param {boolean} silent メッセージ非表示
 */
function applySearch(silent = false) {
    currentSearch.name = document.getElementById("search-name").value.trim();
    currentSearch.department = document.getElementById("search-department").value.trim();
    currentSearch.grade = document.getElementById("search-grade").value.trim();
    currentSearch.role = document.getElementById("search-role").value.trim();
    currentSearch.room = document.getElementById("search-room").value.trim();

    const { name, department, grade, role, room } = currentSearch;

    if (!name && !department && !grade && !role && !room) {
        renderTable(allStatusData);
        if (!silent) {
            showMessage("すべての対応状況を表示しています");
        }
        return;
    }

    const filtered = allStatusData.filter(item => {
        if (name && !item.name.toLowerCase().includes(name.toLowerCase())) return false;
        if (department && !item.department.toLowerCase().includes(department.toLowerCase())) return false;
        if (grade && !item.grade.toLowerCase().includes(grade.toLowerCase())) return false;
        if (role && !item.role.toLowerCase().includes(role.toLowerCase())) return false;
        if (room && !item.room.toLowerCase().includes(room.toLowerCase())) return false;
        return true;
    });

    renderTable(filtered);

    if (!silent) {
        if (filtered.length === 0) {
            showMessage("該当する人物が見つかりません", true);
        } else {
            showMessage(`${filtered.length} 件の結果が見つかりました`);
        }
    }
}

/**
 * テーブルを描画する
 * @param {Array} data 表示対象データ
 */
function renderTable(data) {
    const tbody = document.querySelector("#status-table tbody");
    tbody.innerHTML = "";

    data.forEach(item => {
        const tr = document.createElement("tr");

        // 在室状況に応じた表示文字列と CSS クラスを決定
        let statusText = "";
        let statusClass = "";

        if (item.status === 1) {
            statusText = "対応可";
            statusClass = "status-ok";
        } else if (item.status === 0) {
            statusText = "対応不可";
            statusClass = "status-ng";
        } else {
            statusText = "未設定";
            statusClass = "status-unknown";
        }

        /*
         * 在室状況セルには status-cell を付与し、
         * バッジ表示用に span 要素を内部に配置する。
         * これにより table の罫線と中央配置を両立する。
         */
        tr.innerHTML = `
        <td>${item.name}</td>
        <td>${item.department}</td>
        <td>${item.role}</td>
        <td>${item.grade}</td>
        <td>${item.room}</td>
        <td class="status-cell">
            <span class="${statusClass}">
                ${statusText}
            </span>
        </td>
        <td>${formatTimestamp(item.timestamp)}</td>
    `;

        tbody.appendChild(tr);
    });


    /**
     * 更新時間(timestamp)を表示用に整形
     * @param {string|null} timestamp
     */
    function formatTimestamp(timestamp) {
        if (!timestamp) return "-";
        const date = new Date(timestamp);
        return date.toLocaleString("ja-JP");
    }

}
/**
 * 検索中か判定する補助関数
 */
function hasActiveSearch() {
    const { name, department, grade, role, room } = currentSearch;
    return !!(name || department || grade || role || room);
}

/**
 * メッセージ表示
 * @param {string} message 表示内容
 * @param {boolean} isError エラー表示かどうか
 */
function showMessage(message, isError = false) {
    const area = document.getElementById("message-area");
    area.textContent = message;
    area.style.color = isError ? "red" : "black";
}
