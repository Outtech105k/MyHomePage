function nowDateTime() {
	// 現在月日を'YYYY/MM/DD'で取得
	let today = new Date();
	today.setDate(today.getDate());
	let yyyy = today.getFullYear();
	let mm = ("0" + (today.getMonth() + 1)).slice(-2);
	let dd = ("0" + today.getDate()).slice(-2);
	return yyyy + '-' + mm + '-' + dd;
}

function drawWaitChart(shop_name, datetype, datevalue) {
	let req = new XMLHttpRequest();		  // XMLHttpRequest オブジェクトを生成する
	req.onreadystatechange = () => {		  // XMLHttpRequest オブジェクトの状態が変化した際に呼び出されるイベントハンドラ
		// サーバーからのレスポンスが完了し、かつ、通信が正常に終了した場合
		//グラフ要素を取得、レスポンス通りに表示
		if (req.readyState == 4 && req.status == 200) { 
			let ctx = document.getElementById("sawayakaWaitChart");
			window.sawayakaWaitChart = new Chart(ctx, JSON.parse(req.responseText));
		}
	};
	// HTTPメソッドとアクセスするサーバーの URL を指定(まだ送信しない)
	// !) 脆弱性の観点から、テンプレートリテラルをクエリパラメータに含めないようにすべき
	req.open(
		"GET",
		`https://techgate.mydns.jp/apis/sawayaka_waiting?shop_name=${shop_name}&datetype=${datetype}&datevalue=${datevalue}`,
		false
	);
	req.send(null); // リクエストを送信
}

function refreshChart(shop_name, datetype, datevalue) {
	// sawayakaWaitChartの削除ができるかどうかで、リセットの必要性を判定
	if (typeof sawayakaWaitChart.destroy === "function") {
		sawayakaWaitChart.destroy();
	}
	// 描画実行
	drawWaitChart(shop_name, datetype, datevalue);
}

function checkDrawChart(check_date_type) {
	// 描画グラフの設定を追加
	const check_shop = document.getElementById("showShopList");
	let check_date_value=null;
	if (check_date_type === 'day') {
		//描画する日付・店舗を取得して描画
		check_date_value = document.getElementById("showDateValue");
	} else if (check_date_type === 'week') {
		//描画する週を取得して描画
		check_date_value = document.getElementById("showWeekValue");
	} else {
		alert('未実装です');
		return;
	}
	if (check_shop.value !== '表示する店舗を選択' && check_date_value.value !== '')
		refreshChart(check_shop.value, check_date_type, check_date_value.value);
	else
		alert('グラフの表示設定が正しくありません');
}

document.addEventListener("DOMContentLoaded", () => {
	const today = nowDateTime();
	refreshChart('', 'day', today);
	document.getElementById("showDateValue").value = today;
});