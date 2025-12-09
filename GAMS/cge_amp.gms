$title Modelo estándar ampliado

$onText
basado en el libro:
Handbook of Computible General Equilibrium Modeling
Hosoe, N, Gasawa, K, and Hashimoto, H
University of Tokyo Press, Tokyo, Japan, 2004
$offText

Set
   u      'SAM entry'  / BRD,MLK,CAP,LAB,IDT,TRF,HOH1,HOH2,HOH3,GOV,AYD,CSS,INV,EXT /
   i(u)   'goods'      / BRD,MLK                                                    /
   h(u)   'factor'     /         CAP,LAB                                            /
   l(u)   'demanda'    /                         HOH1,HOH2,HOH3                     /;

Alias (u,v), (i,j), (h,k), (l,n);
Parameter SAM(u,v);

$onEmbeddedCode Connect:
- ExcelReader:
    file: C:\FIDELIO\CGE_10\Datos\SAM_AMPLIADA.xlsx
    symbols:
      - name: SAM
        range: Hoja1!A1:O15
        columnDimension: 1
        rowDimension: 1
- GAMSWriter:
    symbols: all
$offEmbeddedCode

$ontext
Table SAM(u,v) 'social accounting matrix'
        BRD     MLK     CAP    LAB     IDT    TRF   HOH1    HOH2     HOH3     GOV     AYD     CSS    INV    EXT
BRD     210      80       0      0       0      0    100     100      130     190       0       0    137     80
MLK     170      90       0      0       0      0    190     100      135     140       0       0    150     40
CAP     290     410       0      0       0      0      0       0        0       0       0       0      0      0
LAB     150     250       0      0       0      0      0       0        0       0       0       0      0      0
IDT      49      38       0      0       0      0      0       0        0       0       0       0      0      0
TRF      10      20       0      0       0      0      0       0        0       0       0       0      0      0
HOH1      0       0     450    100       0      0      0       0        0       0       7       0      0      0
HOH2      0       0      50    300       0      0      0       0        0       0       0       0      0      0
HOH3      0       0     200      0       0      0      0       0        0       0       0      80      0      0
GOV       0       0       0      0      87     30    157      60        0       0       0       0      0      0
AYD       0       0       0      0       0      0      0       0        0       7       0       0      0      0
CSS      15      20       0      0       0      0     10      20       15       0       0       0      0      0
INV       0       0       0      0       0      0    100      70        0      -3       0       0      0    120
EXT     133     107       0      0       0      0      0       0        0       0       0       0      0      0;
$offText

display SAM;

* Loading the initial values
Parameter
   Y0(j)     'composite factor'
   F0(h,j)   'the h-th factor input by the j-th firm'
   X0(i,j)   'intermediate input'
   Z0(j)     'output of the j-th good'
   Xp0(l,i)  'household consumption of the i-th good '
   Xg0(i)    'government consumption'
   Xv0(i)    'investment demand'
   E0(i)     'exports'
   M0(i)     'imports'
   Q0(i)     "Armington's composite good"
   tauz(i)   'production tax rate'
   D0(i)     'domestic good'
   Sp0(l)    'private saving'
   Sg0       'government saving'
   Td0(l)    'direct tax'
   Tz0(j)    'production tax'
   Tm0(j)    'import tariff'
   FF(l,h)   'factor endowment of the h-th factor'
   Sf        'foreign saving in US dollars'
   CssH0(l)  'pagos a la seguridad social de los hogares'
   CssE0(i)  'pagos a la seguridad social de las empresas'
   PssH0(l)  'pensiones'
   AgE0(i)   'ayudas del gobierno a las empresas'
   AgH0(l)   'ayudas del gobierno a los hogares'
   pWe(i)    'export price in US dollars'
   pWm(i)    'import price in US dollars'
;
Td0(l)    = SAM("GOV",l);
Tz0(j)    = SAM("IDT",j);
Tm0(j)    = SAM("TRF",j);
F0(h,j)   = SAM(h,j);
Y0(j)     = sum(h, F0(h,j));
X0(i,j)   = SAM(i,j);
Z0(j)     = Y0(j)+sum(i,X0(i,j));
M0(i)     = SAM("EXT",i);
CssE0(i)  = SAM("CSS",i);
CssH0(l)  = SAM("CSS",l);
PssH0(l)  = SAM(l,"CSS");
AgE0(i)   = SAM(i,'AYD');
AgH0(l)   = SAM(l,'AYD');
Xp0(l,i)  = SAM(i,l);
FF(l,h)   = SAM(l,h);
Xg0(i)    = SAM(i,"GOV");
Xv0(i)    = SAM(i,"INV");
E0(i)     = SAM(i,"EXT");
Q0(i)     = sum(l, Xp0(l,i))+Xg0(i)+Xv0(i)+sum(j,X0(i,j));
tauz(j)   = Tz0(j)/Z0(j);
D0(i)     = (1+tauz(i))*Z0(i)-E0(i)+CssE0(i)-AgE0(i);
Sp0(l)    = SAM("INV",l);
Sg0       = SAM("INV","GOV");
Sf        = SAM("INV","EXT");
pWe(i)    = 1.;
pWm(i)    = 1.;

display FF,F0,Y0,X0,Xp0,Xg0,Xv0,Q0,Z0,E0,M0,D0,Td0,Tz0,Tm0,Sp0,AgE0,AgH0,Sg0,Sf,
        CssE0,CssH0,PssH0;
        
* Calibration
Parameter
   sigma(i) 'elasticity of substitution'
   psi(i)   'elasticity of transformation'
   eta(i)   'substitution elasticity parameter'
   phi(i)   'transformation elasticity parameter';

sigma(i) =  2;
psi(i)   =  2;
eta(i)   = (sigma(i) - 1)/sigma(i);
phi(i)   = (psi(i) + 1)/psi(i);

Parameter
   alpha(l,i) 'share parameter in utility func.'
   beta(h,j)  'share parameter in production func.'
   b(j)       'scale parameter in production func.'
   ax(i,j)    'intermediate input requirement coeff.'
   ay(j)      'composite fact. input req. coeff.'
   mu(i)      'government consumption share'
   lambda(i)  'investment demand share'
   deltam(i)  'share par. in Armington func.'
   deltad(i)  'share par. in Armington func.'
   gamma(i)   'scale par. in Armington func.'
   xid(i)     'share par. in transformation func.'
   xie(i)     'share par. in transformation func.'
   theta(i)   'scale par. in transformation func.'
   ssp(l)     'average propensity for private saving'
   ssg        'average propensity for gov. saving'
   taud(l)    'direct tax rate'
   taum(i)    'import tariff rate'
   ctzsse(i)  'tipo seg.social empresas'
   ctzssh(l)  'tipo seg.social hogares',
   cage(i)    'coeficiente ayuda gobierno empresas'
   cagh(l)    'coeficiente ayuda gobierno hogares';

alpha(l,i)  =  Xp0(l,i)/sum(j, Xp0(l,j));
beta(h,j)   =  F0(h,j)/sum(k, F0(k,j));
b(j)        =  Y0(j)/prod(h, F0(h,j)**beta(h,j));
ax(i,j)     =  X0(i,j)/Z0(j);
ay(j)       =  Y0(j)/Z0(j);
mu(i)       =  Xg0(i)/sum(j, Xg0(j));
lambda(i)   =  Xv0(i)/(sum(l,Sp0(l))+Sg0+Sf);
taum(j)     =  Tm0(j)/M0(j);
deltam(i)   = (1+taum(i))*M0(i)**(1-eta(i))/((1+taum(i))*M0(i)**(1-eta(i)) + D0(i)**(1-eta(i)));
deltad(i)   =  D0(i)**(1-eta(i))/((1+taum(i))*M0(i)**(1-eta(i)) + D0(i)**(1-eta(i)));
gamma(i)    =  Q0(i)/(deltam(i)*M0(i)**eta(i)+deltad(i)*D0(i)**eta(i))**(1/eta(i));
xie(i)      =  E0(i)**(1-phi(i))/(E0(i)**(1-phi(i))+D0(i)**(1-phi(i)));
xid(i)      =  D0(i)**(1-phi(i))/(E0(i)**(1-phi(i))+D0(i)**(1-phi(i)));
theta(i)    =  Z0(i)/(xie(i)*E0(i)**phi(i)+xid(i)*D0(i)**phi(i))**(1/phi(i));
ssp(l)      =  Sp0(l)/(sum(h, FF(l,h))+ PssH0(l));
ssg         =  Sg0/(sum(l,Td0(l))+sum(j,Tz0(j))+sum(j,Tm0(j))-sum(j,AgE0(j))-sum(l,AgH0(l)));
taud(l)     =  Td0(l)/(sum(h, FF(l,h))+ PssH0(l));
taum(j)     =  Tm0(j)/M0(j);
ctzsse(i)   =  CssE0(i)/F0("LAB",i);
ctzssh(l)   =  CssH0(l)/(FF(l,"LAB")+PssH0(l));
cage(i)     =  AgE0(i) / (sum(n,Td0(n)) + sum(j,Tz0(j)) + sum(j,Tm0(j)));
cagh(l)     =  AgH0(l) / (sum(n,Td0(n)) + sum(j,Tz0(j)) + sum(j,Tm0(j)));

display phi,tauz,taum,alpha,beta,b,ax,ay,mu,lambda,deltam,deltad,gamma,xie,xid,
        theta,ssp,ssg,taud,ctzsse,ctzssh,cage,cagh;

Variable
   pf(h)    'the h-th factor price'
   py(j)    'composite factor price'
   pz(j)    'supply price of the i-th good'
   pq(i)    "Armington's composite good price"
   pd(i)    'the i-th domestic good price'
   epsilon  'exchange rate'
   pe(i)    'export price in local currency'
   pm(i)    'import price in local currency'
   Y(j)     'composite factor'
   F(h,j)   'the h-th factor input by the j-th firm'
   X(i,j)   'intermediate input'
   Td(l)    'direct tax'
   Tz(j)    'production tax'
   Tm(i)    'import tariff'
   AgE(i)   'ayudas del gobierno a las empresas'
   AgH(l)   'ayudas del gobierno a los hogares'
   Sp(l)    'private saving'
   Sg       'government saving'
   Xg(i)    'government consumption'
   CssH(l)  'pagos a la seguridad social de los hogares'
   CssE(i)  'pagos a la seguridad social de las empresas'
   Xv(i)    'investment demand'
   Xp(l,i)  'household consumption of the i-th good'
   Q(i)     "Armington's composite good"
   M(i)     'imports'
   D(i)     'domestic good'
   Z(j)     'output of the j-th good'
   E(i)     'exports'
   UU       'utility [fictitious]';

Equation
   eqepsilon   'balance of payments'
   eqpe(i)     'world export price equation'
   eqpm(i)     'world import price equation'
   eqpy(j)     'composite factor agg. func.'
   eqF(h,j)    'factor demand function'
   eqX(i,j)    'intermediate demand function'
   eqY(j)      'composite factor demand function'
   eqpzs(j)    'unit cost function'
   eqTd(l)     'direct tax revenue function'
   eqTz(j)     'production tax revenue function'
   eqTm(i)     'import tariff revenue function'
   eqAgE(i)    'ayudas del gobierno a los hogares'
   eqAgH(l)    'ayudas del gobierno a los hogares'
   eqSp(l)     'private saving function'
   eqSg        'government saving function'
   eqXg(i)     'government demand function'
   eqctzsse(i) 'cotización seg social empresas'
   eqctzssh(l) 'cotización seg social hogares'
   eqXv(i)     'investment demand function'
   eqXp(l,i)   'household demand function'
   eqpqs(i)    'Armington function'
   eqM(i)      'import demand function'
   eqD(i)      'domestic good demand function'
   eqpzd(i)    'transformation function'
   eqDs(i)     'domestic good supply function'
   eqE(i)      'export supply function'
   eqpqd(i)    'market clearing cond. for comp. good'
   eqpf(h)     'factor market clearing condition'
   obj         'utility function [fictitious]';

* domestic production
eqpe(i)..     pe(i)   =e= epsilon*pWe(i);

eqpm(i)..     pm(i)   =e= epsilon*pWm(i);

eqpy(j)..     Y(j)    =e= b(j)*prod(h, F(h,j)**beta(h,j));

eqF(h,j)..    F(h,j)  =e= beta(h,j)*py(j)*Y(j)/pf(h);

eqX(i,j)..    X(i,j)  =e= ax(i,j)*Z(j);

eqY(j)..      Y(j)    =e= ay(j)*Z(j);

eqpzs(j)..    pz(j)   =e= ay(j)*py(j)+sum(i,ax(i,j)*pq(i));

* government behavior
eqTd(l)..     Td(l)   =e= taud(l) * (sum(h,pf(h)*FF(l,h))+PssH0(l));

eqTz(j)..     Tz(j)   =e= tauz(j)*pz(j)*Z(j);

eqTm(i)..     Tm(i)   =e= taum(i)*pm(i)*M(i);

eqAgE(i)..    AgE(i)  =e= cage(i) * (sum(n,Td(n))+sum(j,Tz(j))+sum(j,Tm(j)));

eqAgH(l)..    AgH(l)  =e= cagh(l) * (sum(n,Td(n))+sum(j,Tz(j))+sum(j,Tm(j)));

eqSp(l)..     Sp(l)   =e= ssp(l) * (sum(h, pf(h)*FF(l,h)) + PssH0(l));

eqSg..        Sg      =e= ssg*(sum(l,Td(l))+sum(j, Tz(j))+sum(j,Tm(j))-sum(j,AgE(j))-sum(l,AgH(l)));

eqXg(i)..     Xg(i)   =e= mu(i)*(sum(l,Td(l))+sum(j,Tz(j))+sum(j,Tm(j))-Sg-sum(j,AgE(j))-sum(l,AgH(l)))/pq(i);

eqctzsse(i).. CssE(i) =e= ctzsse(i) * F('LAB',i);

eqctzssh(l).. CssH(l) =e= ctzssh(l) * (FF[l,'LAB'] + PssH0(l));

* investment behavior
eqXv(i)..     Xv(i)   =e= lambda(i)*(sum(l,Sp(l))+Sg+epsilon*Sf)/pq(i);

* savings

* household consumption
eqXp(l,i)..   Xp(l,i) =e= alpha(l,i) * (sum(h,pf(h)*FF(l,h))+AgH(l)+PssH0(l)-(Sp(l)+Td(l)+CssH(l)))/pq(i);

* international trade
eqepsilon.. sum(i,pWe(i)*E(i))+Sf =e= sum(i,pWm(i)*M(i));

* Armington function
eqpqs(i)..  Q(i)      =e=  gamma(i)*(deltam(i)*M(i)**eta(i) + deltad(i)*D(i)**eta(i))**(1/eta(i));

eqM(i)..    M(i)      =e= (gamma(i)**eta(i)*deltam(i)*pq(i)/((1+taum(i))*pm(i)))**(1/(1-eta(i)))*Q(i);

eqD(i)..    D(i)      =e= (gamma(i)**eta(i)*deltad(i)*pq(i)/pd(i))**(1/(1-eta(i)))*Q(i);

* transformation function
eqpzd(i)..  Z(i)      =e=  theta(i)*(xie(i)*E(i)**phi(i)+xid(i)*D(i)**phi(i))**(1/phi(i));

eqE(i)..    E(i)      =e= (theta(i)**phi(i)*xie(i)*(1+tauz(i)+CssE(i)/Z(i)-AgE(i)/Z(i))*pz(i)/pe(i))**(1/(1-phi(i)))*Z(i);

eqDs(i)..   D(i)      =e= (theta(i)**phi(i)*xid(i)*(1+tauz(i)+CssE(i)/Z(i)-AgE(i)/Z(i))*pz(i)/pd(i))**(1/(1-phi(i)))*Z(i);

* market clearing condition
eqpqd(i)..  Q(i)      =e= sum(l, Xp(l,i)) + Xg(i) + Xv(i) + sum(j, X(i,j));

eqpf(h)..   sum(j, F(h,j)) =e= sum(l,FF(l,h));
* fictitious objective function
obj..       UU        =e= sum(l, prod(i, Xp(l,i)**alpha(l,i)));

* Initializing variables
pf.l(h)   = 1.;
py.l(j)   = 1.;
pz.l(j)   = 1.;
pq.l(i)   = 1.;
pe.l(i)   = 1.;
pm.l(i)   = 1.;
pd.l(i)   = 1.;
epsilon.l = 1.;
Y.l(j)    = Y0(j);
F.l(h,j)  = F0(h,j);
X.l(i,j)  = X0(i,j);
Z.l(j)    = Z0(j);
Xp.l(l,i) = Xp0(l,i);
Xg.l(i)   = Xg0(i);
Xv.l(i)   = Xv0(i);
E.l(i)    = E0(i);
M.l(i)    = M0(i);
Q.l(i)    = Q0(i);
D.l(i)    = D0(i);
Sp.l(l)   = Sp0(l);
Sg.l      = Sg0;
Td.l(l)   = Td0(l);
Tz.l(j)   = Tz0(j);
Tm.l(i)   = Tm0(i);
CssH.l(l) = CssH0(l);
CssE.l(i) = CssE0(i);
AgE.l(i)  = AgE0(i);
AgH.l(l)  = AgH0(l);

* Setting lower bounds to avoid division by zero
* hay que admitir el 0 para aquellas variables que resultarán con valor 0 al aplicar
* las ecuaciones, como:
*   las ayudas del gobierno que tienen coeficiente 0,
*   el Sp para HOH3
*   los Td para HOH3
* un valor 0 de inicio no es problema porque GAMS lo cambia automáticamente al valo 'lo'
pf.lo(h)    = 0.000001;
py.lo(j)    = 0.000001;
pz.lo(j)    = 0.000001;
pq.lo(i)    = 0.000001;
pe.lo(i)    = 0.000001;
pm.lo(i)    = 0.000001;
pd.lo(i)    = 0.000001;
epsilon.lo  = 0.000001;
Y.lo(j)     = 0.000001;
F.lo(h,j)   = 0.000001;
X.lo(i,j)   = 0.000001;
Z.lo(j)     = 0.000001;
Xp.lo(l,i)  = 0.000001;
Xg.lo(i)    = 0.000001;
Xv.lo(i)    = 0.000001;
E.lo(i)     = 0.000001;
M.lo(i)     = 0.000001;
Q.lo(i)     = 0.000001;
D.lo(i)     = 0.000001;
Sp.lo(l)    = 0.00000;
Td.lo(l)    = 0.00000;
Tz.lo(j)    = 0.000001;
Tm.lo(i)    = 0.000001;
CssH.lo(l)  = 0.000001;
CssE.lo(i)  = 0.000001;
AgE.lo(i)   = 0.00000;
AgH.lo(l)   = 0.00000;

* para evitar infactibilidad, ya que partimos de déficit público, ahorro (Sg) = -3
* que hace que el coeficiente de ahorro (ssg) sea negativo y al aplicar la función que
* calcula Sg produzca valores negativos
Sg.lo       = -100.;

* numeraire
* con pf.fx hacemos que pf.lo y pf.up sean 1, lo que significa que pf sólo puede valer 1
pf.fx("LAB") = 1;

Model stdcge / all /;

*option limrow = 6 ;

* para no buscat una solución y simplemente aplicat las ecuaciones con los valores de partida
*stdcge.iterlim = 1

solve stdcge maximizing UU using nlp;

*Parameter
*    tt(l);
*tt(l) = cagh(l) * (sum(n,Td.l(n))+sum(j,Tz.l(j))+sum(j,Tm.l(j)));

*display 'Comprobación de AgH'
*display tt,cagh,Td.l,Tz.l,Tm.l;

execute_unload 'solucion3H1.gdx'
   Y.l,
   F.l,
   FF,
   X.l,
   Z.l,
   Xp.l,
   Xg.l,
   Xv.l,
   E.l,
   M.l,
   Q.l,
   D.l,
   pf.l,
   py.l,
   pz.l,
   pq.l,
   pe.l,
   pm.l,
   pd.l,
   epsilon,
   Sp.l,
   Sg.l,
   Td.l,
   Tz.l,
   Tm.l,
   CssH.l,
   CssE.l,
   PssH0,
   AgE.l,
   AgH.l,
   Sf,
   alpha,
   beta,
   b,
   ax,
   ay,
   mu,
   lambda,
   deltam,
   deltad,
   gamma,
   xid,
   xie,
   theta,
   ssp,
   ssg,
   taud,
   tauz,
   taum,
   ctzsse,
   ctzssh,
   cage,
   cagh
;

Parameter
    qq(i);
qq(i) = sum(l,Xp.l(l,i))+Xg.l(i)+Xv.l(i)+sum(j,X.l(i,j));

display 'Comprobación del cierre'
display qq;
display Q.l;

Parameter
   UU0(l) 'utility level in the base run eq.'
   ep0(l) 'expenditure func. in the base run eq.'
   ep1(l) 'expenditure func. in the C-f eq.'
   EV(l)  'Hicksian equivalent variations';

UU0(l) = prod(i, Xp0(l,i)**alpha(l,i));
ep0(l) = UU0(l) /prod(i, (alpha(l,i)/1)**alpha(l,i));
ep1(l) = (prod(i,Xp.l(l,i)**alpha(l,i))) /prod(i, (alpha(l,i)/1)**alpha(l,i));
EV(l)  = ep1(l) - ep0(l);

display EV;

* Incremento del 10% para los factores prestados por los hogares

FF(l,h) = 1.1 * FF(l,h);

pf.fx("LAB") = 1;

* Si se fija el valor de pf.lo("LAB") el modelo se vuelve infactible
pf.lo("LAB") = -inf;
pf.up("LAB") = +inf;

option bRatio = 1;

solve stdcge maximizing UU using nlp;

execute_unload 'solucion3H2.gdx'
   Y.l,
   F.l,
   FF,
   X.l,
   Z.l,
   Xp.l,
   Xg.l,
   Xv.l,
   E.l,
   M.l,
   Q.l,
   D.l,
   pf.l,
   py.l,
   pz.l,
   pq.l,
   pe.l,
   pm.l,
   pd.l,
   epsilon,
   Sp.l,
   Sg.l,
   Td.l,
   Tz.l,
   Tm.l,
   CssH.l,
   CssE.l,
   PssH0,
   AgE.l,
   AgH.l,
   Sf,
   alpha,
   beta,
   b,
   ax,
   ay,
   mu,
   lambda,
   deltam,
   deltad,
   gamma,
   xid,
   xie,
   theta,
   ssp,
   ssg,
   taud,
   tauz,
   taum,
   ctzsse,
   ctzssh,
   cage,
   cagh
;

Parameter
    qq(i);
qq(i) = sum(l,Xp.l(l,i))+Xg.l(i)+Xv.l(i)+sum(j,X.l(i,j));

display 'Comprobación del cierre'
display qq;
display Q.l;

Parameter
   UU0(l) 'utility level in the base run eq.'
   ep0(l) 'expenditure func. in the base run eq.'
   ep1(l) 'expenditure func. in the C-f eq.'
   EV(l)  'Hicksian equivalent variations';

UU0(l) = prod(i, Xp0(l,i)**alpha(l,i));
ep0(l) = UU0(l) /prod(i, (alpha(l,i)/1)**alpha(l,i));
ep1(l) = (prod(i,Xp.l(l,i)**alpha(l,i))) /prod(i, (alpha(l,i)/1)**alpha(l,i));
EV(l)  = ep1(l) - ep0(l);

display EV;

