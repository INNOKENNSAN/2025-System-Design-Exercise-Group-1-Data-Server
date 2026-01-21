// templates/js/view.js

/**
 * 閲覧画面用 JavaScript
 * 在室状況の取得および全文一致検索を行う
 */

let allStatusData = []; // 取得した全データを保持

document.addEventListener("DOMContentLoaded", () => {
    // 初期表示（全件）
    loadStatusData();

    // 検索ボタン押下時の処理
    document.getElementById("search-button")
        .addEventListener("click", applySearch);
});

/**
 * 在室状況データを API から取得する
 */
function loadStatusData() {
    fetch("/api/status_view")
        .then(response => response.json())
        .then(data => {
            if (data.result !== "ok") {
                throw new Error("API error");
            }

            allStatusData = data.records.sort((a, b) => a.id - b.id);
            renderTable(allStatusData);

        })
        .catch(() => {
            showMessage("在室状況の取得に失敗しました", true);
        });
}

/**
 * 検索条件を取得し、全文一致で絞り込みを行う
 */
function applySearch() {
    const name = document.getElementById("search-name").value.trim();
    const department = document.getElementById("search-department").value.trim();
    const grade = document.getElementById("search-grade").value.trim();
    const role = document.getElementById("search-role").value.trim();
    const room = document.getElementById("search-room").value.trim();

    // すべて未指定の場合は全件表示
    if (!name && !department && !grade && !role && !room) {
        renderTable(allStatusData);
        showMessage("すべての対応状況を表示しています");
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

    if (filtered.length === 0) {
        showMessage("該当する人物が見つかりません", true);
    } else {
        showMessage(`${filtered.length} 件の結果が見つかりました`);
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
 * メッセージ表示
 * @param {string} message 表示内容
 * @param {boolean} isError エラー表示かどうか
 */
function showMessage(message, isError = false) {
    const area = document.getElementById("message-area");
    area.textContent = message;
    area.style.color = isError ? "red" : "black";
}
