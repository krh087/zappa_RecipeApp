// 材料 / 分量の追加
function addInputFields() {
    const container = document.getElementById("dynamic-input-container");

    // 新しい行を格納する div を作成
    const row = document.createElement("div");
    row.classList.add("input-group", "mb-2");

    // 材料名の入力欄
    const nameInput = document.createElement("input");
    nameInput.type = "text";
    nameInput.name = "dynamic_ingredient[]";
    nameInput.classList.add("form-control");
    nameInput.placeholder = "（例）パスタ";
    nameInput.required = true;

    // 分量の入力欄
    const quantityInput = document.createElement("input");
    quantityInput.type = "text";
    quantityInput.name = "dynamic_quantity[]";
    quantityInput.classList.add("form-control");
    quantityInput.placeholder = "（例）100g";
    quantityInput.required = true;

    // 削除ボタン
    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.textContent = "削除";
    removeButton.classList.add("btn", "btn-danger", "ms-2");
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

// 手順の追加
function addInputFields2() {
    const container = document.getElementById("dynamic-input-container2");

    // 新しい行を格納する div を作成
    const row = document.createElement("div");
    row.classList.add("input-group", "mb-2");

    // 手順の入力欄
    const instructionInput = document.createElement("input");
    instructionInput.type = "text";
    instructionInput.name = "dynamic_instruction[]";
    instructionInput.classList.add("form-control");
    instructionInput.placeholder = "(例)にんにくを刻み、オイルとにんにくを弱火で炒める";
    instructionInput.required = true;

    // 削除ボタン
    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.textContent = "削除";
    removeButton.classList.add("btn", "btn-danger", "ms-2");
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
