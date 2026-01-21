// templates/js/admin.js

/**
 * 管理画面用 JavaScript
 * 人物情報の取得・追加・更新・削除を行う
 */

document.addEventListener("DOMContentLoaded", () => {
    loadPeople();

    document.getElementById("add-row-button")
        .addEventListener("click", addEmptyRow);

    document.getElementById("save-button")
        .addEventListener("click", saveChanges);
});

/**
 * 人物一覧を取得しテーブルに表示する
 */
function loadPeople() {
    fetch("/api/admin?action=list")
        .then(response => response.json())
        .then(json => {
            if (json.result !== "ok" || !Array.isArray(json.data)) {
                throw new Error("invalid response format");
            }

            // ★ 追加：ID 昇順にソート
            json.data.sort((a, b) => a.id - b.id);

            const tbody = document.querySelector("#people-table tbody");
            tbody.innerHTML = "";

            json.data.forEach(person => {
                tbody.appendChild(createRow(person));
            });
        })
        .catch(() => {
            showMessage("人物一覧の取得に失敗しました", true);
        });
}



/**
 * テーブル行を生成する
 * @param {Object} person 人物データ
 */
function createRow(person) {
    const tr = document.createElement("tr");
    tr.dataset.id = person.id;

    tr.innerHTML = `
        <td>${person.id}</td>
        <td><input type="text" name="name" value="${person.name}"></td>
        <td><input type="text" name="department" value="${person.department}"></td>
        <td><input type="text" name="grade" value="${person.grade}"></td>
        <td><input type="text" name="role" value="${person.role}"></td>
        <td><input type="text" name="room" value="${person.room}"></td>
        <td><input type="checkbox" name="delete"></td>
    `;

    return tr;
}

/**
 * 空行（新規追加用）を追加する
 */
function addEmptyRow() {
    const tbody = document.querySelector("#people-table tbody");
    const tr = document.createElement("tr");

    tr.dataset.new = "true";

    tr.innerHTML = `
        <td>新規</td>
        <td><input type="text" name="name"></td>
        <td><input type="text" name="department"></td>
        <td><input type="text" name="grade"></td>
        <td><input type="text" name="role"></td>
        <td><input type="text" name="room"></td>
        <td><input type="checkbox" name="delete"></td>
    `;

    tbody.appendChild(tr);
}

/**
 * 変更内容を保存する
 */
function saveChanges() {
    const rows = document.querySelectorAll("#people-table tbody tr");

    const records = [];
    const deleteIds = [];

    rows.forEach(tr => {
        const isDelete = tr.querySelector('input[name="delete"]').checked;

        // 既存行かつ delete チェックあり → 削除対象
        if (isDelete && tr.dataset.id) {
            deleteIds.push(tr.dataset.id);
            return;
        }

        // 新規行 + delete チェック → 何もしない
        if (isDelete) {
            return;
        }

        const record = {
            name: tr.querySelector('input[name="name"]').value,
            department: tr.querySelector('input[name="department"]').value,
            grade: tr.querySelector('input[name="grade"]').value,
            role: tr.querySelector('input[name="role"]').value,
            room: tr.querySelector('input[name="room"]').value
        };

        // 既存行のみ id を付与
        if (tr.dataset.id) {
            record.id = Number(tr.dataset.id);
        }

        records.push(record);
    });

    // ① 削除 API をすべて実行
    Promise.all(
        deleteIds.map(id =>
            fetch(`/api/admin?action=delete&person_id=${id}`)
        )
    )
    // ② 削除完了後、bulk_update
    .then(() => {
        const encoded = encodeURIComponent(JSON.stringify(records));
        return fetch(`/api/admin?action=bulk_update&records=${encoded}`);
    })
    .then(response => response.json())
    .then(json => {
        if (json.result !== "ok") {
            throw new Error(json.reason || "bulk_update_failed");
        }

        showMessage("保存が完了しました");
        loadPeople();
    })
    .catch(() => {
        showMessage("保存中にエラーが発生しました", true);
    });
}

/**
 * メッセージ表示
 */
function showMessage(message, isError = false) {
    const area = document.getElementById("message-area");
    area.textContent = message;
    area.style.color = isError ? "red" : "black";
}
