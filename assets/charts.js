
const HOT='#FF4D2E',GOLD='#E9C46A',BLUE='#4C8DFF',GREEN='#38D39F',TXT='#F5F7FA',MUT='#9AA7BC',LINE='rgba(255,255,255,.07)';
Chart.defaults.font.family="'Hanken Grotesk',sans-serif";
Chart.defaults.font.size=15;Chart.defaults.color=MUT;
const PAL=[HOT,GOLD,BLUE,GREEN,'#B96BFF','#FF8B73','#5EE0C0','#8FB6FF','#FFD98E','#FF6FA5'];
function grad(ctx,a,b){const g=ctx.createLinearGradient(0,0,0,380);g.addColorStop(0,a);g.addColorStop(1,b);return g;}
const gridX={grid:{color:LINE,drawBorder:false},ticks:{font:{size:15}}};
const gridY={grid:{color:LINE,drawBorder:false},ticks:{font:{size:15},precision:0},beginAtZero:true};
const noLeg={legend:{display:false}};
const TT={backgroundColor:'#0B0F17',borderColor:'#2C3A4E',borderWidth:1,titleColor:TXT,bodyColor:'#D6E1F2',
 padding:14,titleFont:{size:16,weight:'700'},bodyFont:{size:15},displayColors:true,cornerRadius:10};

new Chart(document.getElementById('c1'),{type:'bar',data:{labels:D.days,datasets:[{label:'Violations',
 data:D.dayVals,backgroundColor:c=>grad(c.chart.ctx,'rgba(255,77,46,.95)','rgba(255,77,46,.30)'),
 borderRadius:7,borderSkipped:false,maxBarThickness:64}]},
 options:{maintainAspectRatio:false,plugins:{...noLeg,tooltip:TT},scales:{x:gridX,y:gridY}}});

new Chart(document.getElementById('c2'),{type:'doughnut',data:{labels:D.catLabels,
 datasets:[{data:D.catVals,backgroundColor:PAL,borderColor:'#0B0F17',borderWidth:3,hoverOffset:14}]},
 options:{maintainAspectRatio:false,cutout:'56%',
 plugins:{legend:{position:'right',labels:{boxWidth:13,boxHeight:13,padding:14,font:{size:15}}},tooltip:TT}}});

new Chart(document.getElementById('c3'),{type:'bar',data:{labels:D.projs,datasets:[{data:D.projVals,
 backgroundColor:(c)=>PAL[c.dataIndex%PAL.length],borderRadius:7,borderSkipped:false,maxBarThickness:70}]},
 options:{indexAxis:'y',maintainAspectRatio:false,plugins:{...noLeg,tooltip:TT},
 scales:{x:gridY,y:{...gridX,grid:{display:false}}}}});

new Chart(document.getElementById('c4'),{type:'bar',data:{labels:D.catLabels,
 datasets:D.sevSets.map((s,i)=>({...s,backgroundColor:[HOT,'#FF8B73',GOLD,BLUE,'#5EE0C0'][i],
 borderRadius:5,borderSkipped:false,maxBarThickness:54}))},
 options:{maintainAspectRatio:false,plugins:{legend:{labels:{boxWidth:13,padding:14,font:{size:15}}},tooltip:TT},
 scales:{x:{...gridX,stacked:true,ticks:{maxRotation:0,minRotation:0,autoSkip:false,font:{size:14}}},y:{...gridY,stacked:true}}}});

new Chart(document.getElementById('c5'),{type:'line',data:{labels:D.days,datasets:[{data:D.cum,
 borderColor:GOLD,borderWidth:3,tension:.32,fill:true,pointRadius:5,pointBackgroundColor:GOLD,
 pointBorderColor:'#0B0F17',pointBorderWidth:2,
 backgroundColor:c=>grad(c.chart.ctx,'rgba(233,196,106,.42)','rgba(233,196,106,0)')}]},
 options:{maintainAspectRatio:false,plugins:{...noLeg,tooltip:TT},scales:{x:gridX,y:gridY}}});

new Chart(document.getElementById('c6'),{type:'bar',data:{labels:D.mprojL,datasets:[{data:D.mprojV,
 backgroundColor:c=>grad(c.chart.ctx,'rgba(76,141,255,.95)','rgba(76,141,255,.28)'),
 borderRadius:7,borderSkipped:false,maxBarThickness:56}]},
 options:{maintainAspectRatio:false,plugins:{...noLeg,tooltip:TT},scales:{x:gridX,y:gridY}}});
