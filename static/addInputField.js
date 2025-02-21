document.addEventListener("DOMContentLoaded", function () {
    // 材料・分量の追加
    function addInputFields() {
        const container = document.getElementById("dynamic-input-container");

        // 材料名の入力欄
        const ingredientInput = document.createElement("input");
        ingredientInput.type = "text";
        ingredientInput.name = "dynamic_ingredient[]";  // 配列にして複数の入力を受け取る
        ingredientInput.placeholder = "（例）パスタ";

        // 分量の入力欄
        const quantityInput = document.createElement("input");
        quantityInput.type = "text";
        quantityInput.name = "dynamic_quantity[]";  // 配列にして複数の入力を受け取る
        quantityInput.placeholder = "（例）100g";

        // 削除ボタン
        const removeButton = document.createElement("button");
        removeButton.type = "button";
        removeButton.textContent = "削除";
        removeButton.onclick = function () {
            container.removeChild(ingredientInput);
            container.removeChild(quantityInput);
            container.removeChild(removeButton);
            container.removeChild(br);
        };

        // 改行要素
        const br = document.createElement("br");

        // コンテナに追加
        container.appendChild(ingredientInput);
        container.appendChild(quantityInput);
        container.appendChild(removeButton);
        container.appendChild(br);
    }

    // 手順の追加
    function addInputFields2() {
        const container = document.getElementById("dynamic-input-container2");

        // 手順の入力欄
        const stepInput = document.createElement("input");
        stepInput.type = "text";
        stepInput.name = "dynamic_instruction[]";  // 配列にして複数の入力を受け取る
        stepInput.placeholder = "(例) にんにくを刻み、オイルとにんにくを弱火で炒める";

        // 削除ボタン
        const removeButton = document.createElement("button");
        removeButton.type = "button";
        removeButton.textContent = "削除";
        removeButton.onclick = function () {
            container.removeChild(stepInput);
            container.removeChild(removeButton);
            container.removeChild(br);
        };

        // 改行要素
        const br = document.createElement("br");

        // コンテナに追加
        container.appendChild(stepInput);
        container.appendChild(removeButton);
        container.appendChild(br);
    }

    // グローバルスコープに関数を追加
    window.addInputFields = addInputFields;
    window.addInputFields2 = addInputFields2;
});
