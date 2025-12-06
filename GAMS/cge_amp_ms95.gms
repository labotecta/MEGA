$title Modelo ampliado con MCS: MCA-ESP-05

$onText
No description.


Hosoe, N, Gasawa, K, and Hashimoto, H
Handbook of Computible General Equilibrium Modeling
University of Tokyo Press, Tokyo, Japan, 2004

Keywords: nonlinear programming, general equilibrium model, social accounting
          matrix, utility maximization problem
$offText

Set
   u      'SAM entry'  / AP1, AP2, AP3, AP4, AP5, AP6, L, K, C1, C2, A-I, CSS, INP, SP, SE, AYD /
   i(u)   'goods'      / AP1, AP2, AP3, AP4, AP5, AP6                                           /
   h(u)   'factor'     /                               L, K                                     /
   l(u)   'demanda'    /                                     C1, C2                             /;

Alias (u,v), (i,j), (h,k), (l,n);

Table SAM(u,v) 'social accounting matrix'
       AP1      AP2       AP3      AP4      AP5    AP6       L       K       C1      C2     A-I     CSS     INP       SP        SE    AYD
AP1    2316       1     25294       23     2774    174       0       0     8118    1111     813       0       0        0      8175   1928
AP2    1461   42947     19623     2589    20463   3422       0       0    15120    2069     309       0       0        0      9065 0.0001
AP3    9256    4288    196336    54375    65046  10935       0       0    87781   12012   55736       0       0     7033    131366   1694
AP4     205     655      1734    97946    21050   1825       0       0     3767     516  145896       0       0        0        88 0.0001
AP5    3980    9878     85260    26081   203868  23912       0       0   307653   42096   42578       0       0    18708     57988 0.0001
AP6  0.0001  0.0001    0.0001   0.0001   0.0001 0.0001       0       0     1878     257  0.0001       0       0   145552        39 0.0001
L      4407    3737     56233    40779   158634  70628       0       0        0       0       0       0       0        0         0      0
K     20471   16143     42859    36758   251643  11109       0       0        0       0       0       0       0        0         0      0
C1        0       0         0        0        0      0  334418  378983        0       0  0.0001  0.0001       0        0         0 0.0001
C2        0       0         0        0        0      0  0.0001  0.0001        0       0  0.0001   96804       0        0         0 0.0001
A-I       0       0         0        0        0      0       0       0   115274   15437       0   20643       0    26295     67683      0
CSS     654    1364     17216    12662    43263  21254       0       0    18548    2486       0       0       0        0         0      0
INP  0.0001    1257    0.0001     2453    16951   4467       0       0    67869    9108       0       0       0      494         0      0
SP        0       0         0        0        0      0       0       0    87393   11712       0       0   98977        0         0      0
SE     7977   36798    191303       16    38310 0.0001       0       0        0       0       0       0       0        0         0      0
AYD       0       0         0        0        0      0       0       0        0       0       0       0       0     3622         0      0;

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
   tauz(i)   'production tax rate'
   taum(i)   'import tariff rate'
   ctzsse(i) 'seg.social empresas'
   ctzssh(l) 'seg.social hogares';

Td0(l)   = SAM("SP",l)+SAM("INP",l);
Tz0(j)   = SAM("INP",j);
Tm0(j)   = 0.000000001;
F0(h,j)  = SAM(h,j);
Y0(j)    = sum(h, F0(h,j));
X0(i,j)  = SAM(i,j);
Z0(j)    = Y0(j) +sum(i, X0(i,j));
M0(i)    = SAM("SE",i);
CssE0(i) = SAM("CSS",i);
CssH0(l) = SAM("CSS",l);
PssH0(l) = SAM(l,"CSS");
AgE0(i)  = SAM(i,'AYD');
AgH0(l)  = SAM(l,'AYD');
tauz(j)  = Tz0(j)/Z0(j);
taum(j)$(M0(j) eq 0)  = 0.;
taum(j)$(M0(j) ne 0)  = Tm0(j)/M0(j);
Xp0(l,i) = SAM(i,l);
FF(l,h)  = SAM(l,h);
Xg0(i)   = SAM(i,"SP");
Xv0(i)   = SAM(i,"A-I");
E0(i)    = SAM(i,"SE");
Q0(i)    = sum(l, Xp0(l,i))+Xg0(i)+Xv0(i)+sum(j, X0(i,j));
D0(i)    = (1+tauz(i))*Z0(i)-E0(i)+CssE0(i)-AgE0(i);
Sp0(l)   = SAM("A-I",l);
Sg0      = SAM("A-I","SP");
Sf       = SAM("A-I","SE");
ctzsse(i) = CssE0(i)/F0('L',i);
ctzssh(l) = CssH0(l)/(FF(l,'L')+PssH0(l));
pWe(i)   = 1;
pWm(i)   = 1;

display FF,F0,Y0,X0,Xp0,Xg0,Xv0,Q0,Z0,E0,M0,D0,Tz0,Tm0,Sp0,Td0,AgE0,AgH0,Sg0,Sf,
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
   cage(i)    'coeficiente ayuda gobierno empresas'
   cagh(l)    'coeficiente ayuda gobierno hogares';

alpha(l,i)  =  Xp0(l,i)/sum(j, Xp0(l,j));
beta(h,j)   =  F0(h,j)/sum(k, F0(k,j));
b(j)        =  Y0(j)/prod(h, F0(h,j)**beta(h,j));
ax(i,j)     =  X0(i,j)/Z0(j);
ay(j)       =  Y0(j)/Z0(j);
mu(i)       =  Xg0(i)/sum(j, Xg0(j));
lambda(i)   =  Xv0(i)/(sum(l,Sp0(l))+Sg0+Sf);
deltam(i)   = (1+taum(i))*M0(i)**(1-eta(i))/((1+taum(i))*M0(i)**(1-eta(i)) + D0(i)**(1-eta(i)));
deltad(i)   =  D0(i)**(1-eta(i))/((1+taum(i))*M0(i)**(1-eta(i)) + D0(i)**(1-eta(i)));
gamma(i)    =  Q0(i)/(deltam(i)*M0(i)**eta(i)+deltad(i)*D0(i)**eta(i))**(1/eta(i));
xie(i)      =  E0(i)**(1-phi(i))/(E0(i)**(1-phi(i))+D0(i)**(1-phi(i)));
xid(i)      =  D0(i)**(1-phi(i))/(E0(i)**(1-phi(i))+D0(i)**(1-phi(i)));
theta(i)    =  Z0(i)/(xie(i)*E0(i)**phi(i)+xid(i)*D0(i)**phi(i))**(1/phi(i));
ssp(l)$((sum(h, FF(l,h))+ PssH0(l)) ne 0) = Sp0(l)/(sum(h, FF(l,h))+ PssH0(l));
ssg         =  Sg0/(sum(l,Td0(l))+sum(j,Tz0(j))+sum(j,Tm0(j))-sum(j,AgE0(j))-sum(l,AgH0(l)));
taud(l)$((sum(h, FF(l,h))+ PssH0(l)) ne 0) = Td0(l)/(sum(h, FF(l,h))+ PssH0(l));
cage(i)     = AgE0(i) / (sum(l,Td0(l)) + sum(j,Tz0(j)) + sum(j,Tm0(j)));
cagh(l)     = AgH0(l) / (sum(n,Td0(n)) + sum(j,Tz0(j)) + sum(j,Tm0(j)));

*display alpha, beta,  b,   ax,  ay, mu, lambda, deltam, deltad, gamma, xie
*        xid, theta, ssp, ssg, taud, eta, phi;

display phi,tauz,taum,alpha,beta,b,ax,ay,mu,lambda,deltam,deltad,gamma,xie,xid,
        theta,ssp,ssg,taud,ctzsse,ctzssh,cage,cagh;

Variable
   Y(j)     'composite factor'
   F(h,j)   'the h-th factor input by the j-th firm'
   X(i,j)   'intermediate input'
   Z(j)     'output of the j-th good'
   Xp(l,i)  'household consumption of the i-th good'
   Xg(i)    'government consumption'
   Xv(i)    'investment demand'
   E(i)     'exports'
   M(i)     'imports'
   Q(i)     "Armington's composite good"
   D(i)     'domestic good'
   pf(h)    'the h-th factor price'
   py(j)    'composite factor price'
   pz(j)    'supply price of the i-th good'
   pq(i)    "Armington's composite good price"
   pe(i)    'export price in local currency'
   pm(i)    'import price in local currency'
   pd(i)    'the i-th domestic good price'
   epsilon  'exchange rate'
   Sp(l)    'private saving'
   Sg       'government saving'
   Td(l)    'direct tax'
   Tz(j)    'production tax'
   Tm(i)    'import tariff'
   CssH(l)  'pagos a la seguridad social de los hogares'
   CssE(i)  'pagos a la seguridad social de las empresas'
*   PssH(l)  'pensiones'
   AgE(i)   'ayudas del gobierno a las empresas'
   AgH(l)   'ayudas del gobierno a los hogares'
   UU       'utility [fictitious]';

Equation
   eqpy(j)     'composite factor agg. func.'
   eqF(h,j)    'factor demand function'
   eqX(i,j)    'intermediate demand function'
   eqY(j)      'composite factor demand function'
   eqpzs(j)    'unit cost function'
   eqTd(l)     'direct tax revenue function'
   eqTz(j)     'production tax revenue function'
   eqTm(i)     'import tariff revenue function'
*   eqPssH(l)   'pensiones'
   eqAgE(i)    'ayudas del gobierno a los hogares'
   eqAgH(l)    'ayudas del gobierno a los hogares'
   eqctzsse(i) 'cotización seg social empresas'
   eqctzssh(l) 'cotización seg social hogares'
   eqXg(i)     'government demand function'
   eqXv(i)     'investment demand function'
   eqSp(l)     'private saving function'
   eqSg        'government saving function'
   eqXp(l,i)   'household demand function'
   eqpe(i)     'world export price equation'
   eqpm(i)     'world import price equation'
   eqepsilon   'balance of payments'
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
eqpy(j)..     Y(j)    =e= b(j)*prod(h, F(h,j)**beta(h,j));

eqF(h,j)..    F(h,j)  =e= beta(h,j)*py(j)*Y(j)/pf(h);

eqX(i,j)..    X(i,j)  =e= ax(i,j)*Z(j);

eqY(j)..      Y(j)    =e= ay(j)*Z(j);

eqpzs(j)..    pz(j)   =e= ay(j)*py(j) + sum(i, ax(i,j)*pq(i));

* government behavior
eqTd(l)..     Td(l)   =e= taud(l) * (sum(h, pf(h)*FF(l,h))+PssH0(l));

eqTz(j)..     Tz(j)   =e= tauz(j)*pz(j)*Z(j);

eqTm(i)..     Tm(i)   =e= taum(i)*pm(i)*M(i);

*eqPssH(l)..   PssH(l) =e= PssH0(l);

eqAgE(i)..    AgE(i)  =e= cage(i) * (sum(l,Td(l))+sum(j,Tz(j))+sum(j,Tm(j)));

eqAgH(l)..    AgH(l)  =e= cagh(l) * (sum(n,Td(n))+sum(j,Tz(j))+sum(j,Tm(j)));

eqXg(i)..     Xg(i)$(mu(i) > 0.0001) =e= mu(i) * (sum(l,Td(l))+sum(j,Tz(j))+sum(j,Tm(j))-Sg-sum(j,AgE(j))-sum(l,AgH(l)))/pq(i);

eqctzsse(i).. CssE(i) =e= ctzsse(i) * F['L',i];

eqctzssh(l).. CssH(l) =e= ctzssh(l) * (FF[l,'L'] + PssH0(l));

* investment behavior
eqXv(i)..     Xv(i)   =e= lambda(i)*(sum(l,Sp(l)) + Sg + epsilon*Sf)/pq(i);

* savings
eqSp(l)..     Sp(l)   =e= ssp(l) * (sum(h, pf(h)*FF(l,h)) + PssH0(l));

eqSg..        Sg      =e= ssg*(sum(l,Td(l)) + sum(j, Tz(j)) + sum(j, Tm(j)));

* household consumption
eqXp(l,i)..   Xp(l,i) =e= alpha(l,i) * (sum(h,pf(h)*FF(l,h))+AgH(l)+PssH0(l)-(Sp(l)+Td(l)+CssH(l)))/pq(i);

* international trade
eqpe(i)..   pe(i)     =e= epsilon*pWe(i);

eqpm(i)..   pm(i)     =e= epsilon*pWm(i);

eqepsilon.. sum(i, pWe(i)*E(i)) + Sf =e= sum(i, pWm(i)*M(i));

* Armington function
eqpqs(i)..  Q(i)      =e=  gamma(i)*(deltam(i)*M(i)**eta(i) + deltad(i)*D(i)**eta(i))**(1/eta(i));

eqM(i)..    M(i)      =e= (gamma(i)**eta(i)*deltam(i)*pq(i)/((1+taum(i))*pm(i)))**(1/(1-eta(i)))*Q(i);

eqD(i)..    D(i)      =e= (gamma(i)**eta(i)*deltad(i)*pq(i)/pd(i))**(1/(1-eta(i)))*Q(i);

* transformation function
eqpzd(i)..  Z(i)      =e=  theta(i)*(xie(i)*E(i)**phi(i)+xid(i)*D(i)**phi(i))**(1/phi(i));

eqE(i)..    E(i)      =e= (theta(i)**phi(i)*xie(i)*(1+tauz(i)+CssE(i)/Z(i)+AgE(i)/Z(i))*pz(i)/pe(i))**(1/(1-phi(i)))*Z(i);

eqDs(i)..   D(i)      =e= (theta(i)**phi(i)*xid(i)*(1+tauz(i)+CssE(i)/Z(i)+AgE(i)/Z(i))*pz(i)/pd(i))**(1/(1-phi(i)))*Z(i);

* market clearing condition
eqpqd(i)..  Q(i)      =e= sum(l, Xp(l,i)) + Xg(i) + Xv(i) + sum(j, X(i,j));

eqpf(h)..   sum(j, F(h,j)) =e= sum(l,FF(l,h));
* fictitious objective function
obj..       UU        =e= sum(l, prod(i, Xp(l,i)**alpha(l,i)));

* Initializing variables
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
pf.l(h)   = 1;
py.l(j)   = 1;
pz.l(j)   = 1;
pq.l(i)   = 1;
pe.l(i)   = 1;
pm.l(i)   = 1;
pd.l(i)   = 1;
epsilon.l = 1;
Sp.l(l)   = Sp0(l);
Sg.l      = Sg0;
Td.l(l)   = Td0(l);
Tz.l(j)   = Tz0(j);
Tm.l(i)   = Tm0(i);
CssH.l(l) = CssH0(l);
CssE.l(i) = CssE0(i);
*PssH.l(l) = PssH0(l);
AgE.l(i)  = AgE0(i);
AgH.l(l)  = AgH0(l);

* Setting lower bounds to avoid division by zero
Y.lo(j)     = 0.00001;
F.lo(h,j)   = 0.00001;
X.lo(i,j)   = 0.00001;
Z.lo(j)     = 0.00001;
Xp.lo(l,i)  = 0.00001;
Xg.lo(i)    = 0.00001;
Xv.lo(i)    = 0.00001;
E.lo(i)     = 0.00001;
M.lo(i)     = 0.00001;
Q.lo(i)     = 0.00001;
D.lo(i)     = 0.00001;
pf.lo(h)    = 0.00001;
py.lo(j)    = 0.00001;
pz.lo(j)    = 0.00001;
pq.lo(i)    = 0.00001;
pe.lo(i)    = 0.00001;
pm.lo(i)    = 0.00001;
pd.lo(i)    = 0.00001;
epsilon.lo  = 0.00001;
Sp.lo(l)    = 0.00001;
Sg.lo       = 0.00001;
Td.lo(l)    = 0.00001;
Tz.lo(j)    = 0.00001;
Tm.lo(i)    = 0.000000001;
CssH.lo(l)  = 0.00001;
CssE.lo(i)  = 0.00001;
*PssH.lo(l)  = 0.00001;
AgE.lo(i)   = 0.00001;
AgH.lo(l)   = 0.00001;

* numeraire
pf.fx("L") = 1;

$Ontext
display de funciones DIS-001
execute_unload eqpy,eqF,eqX,eqY,eqpzs,eqTd,eqTz,eqTm,eqXg,eqXv
                            ,eqSp,eqSg,eqXp,eqpe,eqpm,eqepsilon,eqpqs,eqM,eqD
                            ,eqpzd,eqDs,eqE,eqpqd,eqpf,eqctzsse,eqctzssh;
display de variables DIS-002
display FF,F.l,Y.l,X.l,Xp.l,Xg.l,Xv.l,Q.l,Z.l,E.l,M.l,D.l,Tz.l,Tm.l,Sp.l,Td.l,AgE.l,AgH.l,
        Sg.l,Sf,CssE.l,CssH.l,PssH.l;
execute_unload 'var.gdx',FF,F.l,Y.l;
execute_unload de funciones EXEUN-001
execute_unload 'parcial.gdx',eqpy.l,eqF.l,eqX.l,eqY.l,eqpzs.l,eqTd.l,eqTz.l,eqTm.l,eqXg.l,eqXv.l
                            ,eqSp.l,eqSg.l,eqXp.l,eqpe.l,eqpm.l,eqepsilon.l,eqpqs.l,eqM.l,eqD.l
                            ,eqpzd.l,eqDs.l,eqE.l,eqpqd.l,eqpf.l,eqctzsse.l,eqctzssh.l;
$Offtext

Model stdcge / all /;

*option limrow = 6 ;

solve stdcge maximizing UU using nlp;
execute_unload 'solucion.gdx'
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

* Incremento de los factores prestados por los hogares

FF(l,h) = 1.1 * FF(l,h);

option bRatio = 1;

solve stdcge maximizing UU using nlp;
execute_unload 'solucion2.gdx'
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
   Sf;

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

$Ontext
execute_unload de funciones EXEUN-002
execute_unload 'funciones.gdx',eqpy.l,eqF.l,eqX.l,eqY.l,eqpzs.l,eqTd.l,eqTz.l,eqTm.l,eqXg.l,eqXv.l
                            ,eqSp.l,eqSg.l,eqXp.l,eqpe.l,eqpm.l,eqepsilon.l,eqpqs.l,eqM.l,eqD.l
                            ,eqpzd.l,eqDs.l,eqE.l,eqpqd.l,eqpf.l,eqctzsse.l,eqctzssh.l;

$gdxin funciones.gdx
$load
display de variables DIS-003
display eqpy.l,eqF.l,eqX.l,eqY.l,eqpzs.l,eqTd.l,eqTz.l,eqTm.l,eqXg.l,eqXv.l
                            ,eqSp.l,eqSg.l,eqXp.l,eqpe.l,eqpm.l,eqepsilon.l,eqpqs.l,eqM.l,eqD.l
                            ,eqpzd.l,eqDs.l,eqE.l,eqpqd.l,eqpf.l,eqctzsse.l,eqctzssh.l;
$Offtext

