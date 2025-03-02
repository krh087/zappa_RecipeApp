// 材料 / 分量の追加・削除
function addInputFields() {
    const container = document.getElementById("dynamic-input-container");

    // 新しい行を格納する div を作成
    const row = document.createElement("div");
    row.classList.add("input-row");

    // 材料名の入力欄
    const nameInput = document.createElement("input");
    nameInput.type = "text";
    nameInput.name = "dynamic_ingredient";
    nameInput.placeholder = "（例）パスタ";
    nameInput.required = true;

    // 分量の入力欄
    const quantityInput = document.createElement("input");
    quantityInput.type = "text";
    quantityInput.name = "dynamic_quantity";
    quantityInput.placeholder = "（例）100g";
    quantityInput.required = true;

    // 削除ボタン
    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.textContent = "削除";
    removeButton.classList.add("remove-btn");
    removeButton.onclick = function () {
        removeRow(this);
    };

    // 要素を行に追加
    row.appendChild(nameInput);
    row.appendChild(quantityInput);
    row.appendChild(removeButton);
    
    // コンテナに行を追加
    container.appendChild(row);
}

// 手順の追加・削除
function addInputFields2() {
    const container = document.getElementById("dynamic-input-container2");

    // 新しい行を格納する div を作成
    const row = document.createElement("div");
    row.classList.add("input-row");

    // 手順の入力欄
    const instructionInput = document.createElement("input");
    instructionInput.type = "text";
    instructionInput.name = "dynamic_instruction";
    instructionInput.placeholder = "(例)にんにくを刻み、オイルとにんにくを弱火で炒める";
    instructionInput.required = true;

    // 削除ボタン
    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.textContent = "削除";
    removeButton.classList.add("remove-btn");
    removeButton.onclick = function () {
        removeRow(this);
    };

    // 要素を行に追加
    row.appendChild(instructionInput);
    row.appendChild(removeButton);

    // コンテナに行を追加
    container.appendChild(row);
}

// 行を削除する関数
function removeRow(button) {
    button.parentElement.remove();
}

// 既存の2行目以降に削除ボタンを追加（材料と手順 両方対応）
document.addEventListener("DOMContentLoaded", function () {
    // 材料（ingredient）の削除ボタン追加
    document.querySelectorAll("#dynamic-input-container .input-row").forEach((row, index) => {
        if (index > 0) { // 2行目以降に削除ボタンを追加
            addDeleteButton(row);
        }
    });

    // 手順（instructions）の削除ボタン追加
    document.querySelectorAll("#dynamic-input-container2 .input-row").forEach((row, index) => {
        if (index > 0) { // 2行目以降に削除ボタンを追加
            addDeleteButton(row);
        }
    });
});

// 削除ボタンを追加する関数
function addDeleteButton(row) {
    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.textContent = "削除";
    removeButton.classList.add("remove-btn");
    removeButton.onclick = function () {
        removeRow(this);
    };
    row.appendChild(removeButton);
}
