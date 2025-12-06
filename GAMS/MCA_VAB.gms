$title Modelo ampliado con MCS: MCA-ESP-05

$onText
basado en el libro:
Handbook of Computible General Equilibrium Modeling
Hosoe, N, Gasawa, K, and Hashimoto, H
University of Tokyo Press, Tokyo, Japan, 2004
$offText

Set
   u      'cuentas de la MCS'  / AP1, AP2, AP3, AP4, AP5, AP6, L, K, C1, C2, A-I, CSS, INP, SP, SE, AYD /
   i(u)   'sectores'           / AP1, AP2, AP3, AP4, AP5, AP6                                           /
   h(u)   'factores'           /                               L, K                                     /
   l(u)   'hogares'            /                                     C1, C2                             /;

Alias (u,v), (i,j), (h,k), (l,n);

Parameter SAM(u,v);
$onEmbeddedCode Connect:
- ExcelReader:
    file: C:\FIDELIO\CGE_AMP\Datos\MCA-ESP-05_ajustada_imp_final.xlsx
    symbols:
      - name: SAM
        range: Hoja1!A1:Q17
        columnDimension: 1
        rowDimension: 1
- GAMSWriter:
    symbols: all
$offEmbeddedCode

display SAM;

* cargando los valores iniciales
Parameter
   Y0(j)     'factor compuesto de las empresas j'
   F0(h,j)   'los factores h empleados por las empresas j'
   X0(i,j)   'inputs intermedios'
   Z0(j)     'producción de las empresas j'
   Xp0(l,i)  'consumo de los hogares l de los productos i'
   Xg0(i)    'consumo del gobierno del producto i'
   Xv0(i)    'demanda de inversión de la empresa i'
   E0(i)     'exportaciones de las empresas i'
   M0(i)     'importaciones de las empresas i'
   Q0(i)     "producto compuesto de Armington de las empresas i"
   D0(i)     'consumo domestico de los productos i'
   Sp0(l)    'ahorro de los hogares l'
   Sg0       'ahorro del gobierno'
   Td0(l)    'impuestos a los hogares l'
   Tz0(j)    'impuestos a las producciones j'
   Tm0(j)    'aranceles a los productos j'
   FF(l,h)  'factores h prestados por los hogares l'
   Sf        'ahorro exterior en moneda local'
   CssH0(l)  'pagos a la seguridad social de los hogares l'
   CssE0(i)  'pagos a la seguridad social de las empresas i'
   PssH0(l)  'pensiones de los hogares l'
   AgE0(i)   'ayudas del gobierno a las empresas i'
   AgH0(l)   'ayudas del gobierno a los hogares l'
   pWe(i)    'precio de exportación en moneda local'
   pWm(i)    'precio de importación en moneda local'
   tauz(i)   'tasa de impuestos a las producciones j'
   taum(i)   'tasa de aranceles a los productos j'
   ctzsse(i) 'tasa de la seg.social a las empresas i'
   ctzssh(l) 'tasa de la seg.social a los hogares l'
   Alp0(l,h)
   DeAd(l,i)
;
Td0(l)   = SAM("SP",l)+SAM("INP",l);
Tz0(j)   = SAM("INP",j);
Tm0(j)   = 0.000001;
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
tauz(j)$(Z0(j) eq 0)  = 0.;
tauz(j)$(Z0(j) ne 0)  = Tz0(j)/Z0(j);
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
ctzssh(l)$(FF(l,'L') eq 0) = 0.;
ctzssh(l)$(FF(l,'L') ne 0) = CssH0(l)/FF(l,'L');
pWe(i)   = 1;
pWm(i)   = 1;
Alp0(l,h) = 0;
DeAd(l,i) = 0;

display FF,F0,Y0,X0,Xp0,Xg0,Xv0,Q0,Z0,E0,M0,D0,Tz0,Tm0,Sp0,Td0,AgE0,AgH0,Sg0,Sf,
        CssE0,CssH0,PssH0,Alp0,DeAd;
        
* calibrado
Parameter
   sigma(i) 'elasticidad de sustitución (importación) de los sectores i'
   psi(i)   'elasticidad de transformación entre local y exportación (CET) de los sectores i'
   eta(i)   'parámetro de elasticidad de sustitución  de los sectores i'
   phi(i)   'parámetro de elasticidad de transformación de los sectores i';

sigma(i) =  2;
psi(i)   =  2;
eta(i)   = (sigma(i) - 1)/sigma(i);
phi(i)   = (psi(i) + 1)/psi(i);

Parameter
   alpha(l,i) 'participación de los productos i en la función de utilidad de los hogares l'
   beta(h,j)  'participación de los factores h en la función de producción de las empresas j'
   b(j)       'parámetro de eswcala de la función de producción de las empresas j'
   ax(i,j)    'coeficietes de los imputs intermedios'
   ay(j)      'coeficiente del input de factor compuesto para las empresas j'
   mu(i)      'participación del producto i en el consumo del gobierno'
   lambda(i)  'participación en la demanda de inversión de las empresas i'
   deltam(i)  'participación de la importación de productos i en la función de Armington'
   deltad(i)  'participación de la producción local de productos i en la función de Armington'
   gamma(i)   'parámetro de escala de la función de producción de Armington de las empresas i'
   xid(i)     'coeficiente de participación en la CET de la demanda local de los sectores i'
   xie(i)     'coeficiente de participación en la CET de la exportación de los sectores i'
   theta(i)   'coeficiente de escala de la CET de exportación de los sectores i'
   ssp(l)     'apropensión al ahorro de los hogares l'
   ssg        'propensión al ahorro del gobierno'
   taud(l)    'tasa de impuestos directos a los hogares l'
   cage(i)    'coeficiente de las ayudas del gobierno a las empresas i'
   cagh(l)    'coeficiente de las ayudas del gobierno a los hogares l'
   alpha_c(l,i)'copia de alpha'
   beta_c(h,j) 'copia'
   rf(l,h)     'parámetro intermedio para calcular Alp'
;
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
ssp(l)$((sum(h, FF(l,h))+ PssH0(l)) eq 0) = 0.;
ssp(l)$((sum(h, FF(l,h))+ PssH0(l)) ne 0) = Sp0(l)/(sum(h, FF(l,h))+ PssH0(l));
ssg         =  Sg0/(sum(l,Td0(l))+sum(j,Tz0(j))+sum(j,Tm0(j))-sum(j,AgE0(j))-sum(l,AgH0(l)));
taud(l)$((sum(h, FF(l,h))+ PssH0(l)) eq 0) = 0.;
taud(l)$((sum(h, FF(l,h))+ PssH0(l)) ne 0) = Td0(l)/(sum(h, FF(l,h))+ PssH0(l));
cage(i)     = AgE0(i) / (sum(n,Td0(n)) + sum(j,Tz0(j)) + sum(j,Tm0(j)));
cagh(l)     = AgH0(l) / (sum(n,Td0(n)) + sum(j,Tz0(j)) + sum(j,Tm0(j)));
rf(l,h)     = FF(l,h) / sum(n,FF(n,h));

alpha_c(l,i)=alpha(l,i);
beta_c(h,j) =beta(h,j)

display phi,tauz,taum,alpha,beta,b,ax,ay,mu,lambda,deltam,deltad,gamma,xie,xid,
        theta,ssp,ssg,taud,ctzsse,ctzssh,cage,cagh,rf;

Variable
   Y(j)     'factor compuesto de los sectores i'
   F(h,i)   'uso de los factores h por los sectores i'
   X(i,j)   'consumo intermedio de los productos i por los sectores j'
   Z(i)     'producción bruta de los sectores i'
   Xp(l,i)  'demanda de los hogares l del producto i'
   Xg(i)    'demanda del gobierno de los productos i'
   Xv(i)    'demanda de inversión de los sectores i'
   E(i)     'exportaciones de los productos i'
   M(i)     'importaciones de los productos i'
   Q(i)     "producción del producto compuesto de Armington por los sectores i"
   D(i)     'demanda local de los productos i'
   pf(h)    'precio de los factores h'
   py(i)    'precio de los factores compuestos i'
   pz(i)    'precio de producir los productos locales i'
   pq(i)    "precio de los productos compuesto de Armington i"
   pe(i)    'precio de exportación de los productos i en moneda local'
   pm(i)    'precio de importación de los productos i en moneda local'
   pd(i)    'precio de los productos i para los compradores locales'
   epsilon  'cotización: moneda local/ moneda extranjera'
   Sp(l)    'ahorro de los hogares l'
   Sg       'ahorro del gobierno'
   Td(l)    'impuestos directos a los hogares l'
   Tz(i)    'impuesto a la producción de los sectores i'
   Tm(i)    'arancel de importación para los productos i'
   CssH(l)  'pagos a la seguridad social de los hogares l'
   CssE(i)  'pagos a la seguridad social de las empresas i'
   AgE(i)   'ayudas del gobierno a las empresas i'
   AgH(l)   'ayudas del gobierno a los hogares l'
   Apz      'holgura de los pseudo impuestos CssE CssH AgE AgH sobre Z'
   Alp(l,h) 'ahorro a largo plazo del factor h por el hogar l'
   UU       'utilidad [ficticia]'
;

Equation
   eqpy(i)     'producción del factor compuesto de los sectores i'
   eqF(h,j)    'uso de los factores h por los sectores i'
   eqX(i,j)    'consumo intermedio de los productos i por los sectores j'
   eqY(i)      'demanda del factor compuesto por los sectores i'
   eqpzs(i)    'precio (coste unitario) de la producción bruta de los sectores i'
   eqTd(l)     'impuestos directos a los hogares l'
   eqTz(i)     'impuesto a la producción de los sectores i'
   eqTm(i)     'arancel de importación para los productos i'
   eqAgE(i)    'ayudas del gobierno a las empresas i'
   eqAgH(l)    'ayudas del gobierno a los hogares l'
   eqSp(l)     'ahorro de los hogares l'
   eqSg        'ahorro del gobierno'
   eqctzsse(i) 'cotización seg social de las empresas i'
   eqctzssh(l) 'cotización seg social de los hogares l'
   eqXg(i)     'demanda del gobierno de los productos i'
   eqXv(i)     'demanda de inversión de los sectores i'
   eqXp(l,i)   'demanda de los hogares l del producto i'
   eqpe(i)     'precio de exportación de los productos i en moneda extranjera'
   eqpm(i)     'precio de importación de los productos i en moneda extranjera'
   eqepsilon   'balanza de pagos'
   eqpqs(i)    'función de Armington para los productos i'
   eqM(i)      'importaciones de los productos i'
   eqD(i)      'demanda local de los productos i'
   eqDs(i)     'sumministro de la demanda local de productos i'
   eqpzd(i)    'producción bruta de la función de transformación'
   eqE(i)      'exportaciones de los productos i'

   eqAlp(l,h)  'ahorro a largo plazo del factor h por el hogar l'

   eqpqd(i)    'condición de equilibrio del mercado para el producto compuesto de los sectores i'
*   eqpf(h)     'condición de equilibrio del mercado para los factores h'
   obj         'utilidad [ficticia]'
;

* comercio internacional
eqpe(i)..   pe(i)     =e= epsilon*pWe(i);
eqpm(i)..   pm(i)     =e= epsilon*pWm(i);
eqepsilon.. sum(i, pWe(i) * E(i)) + Sf =e= sum(i, pWm(i) * M(i));
* producción factor compuesto
eqpy(j)..     Y(j)    =e= b(j)*prod(h, F(h,j) ** beta(h,j));
eqF(h,j)..    F(h,j)  =e= beta(h,j) * py(j) * Y(j) / pf(h);
eqX(i,j)..    X(i,j)  =e= ax(i,j) * Z(j);
eqY(j)..      Y(j)    =e= ay(j) * Z(j);
eqpzs(j)..    pz(j)   =e= ay(j)*py(j) + sum(i, ax(i,j) * pq(i));
* gobierno
* Alp paga impuestos
eqTd(l)..     Td(l)   =e= taud(l) * (sum(h, pf(h) * (FF(l,h) + Alp(l,h))) + PssH0(l));
eqTz(j)..     Tz(j)   =e= tauz(j) * pz(j)*Z(j);
eqTm(i)..     Tm(i)   =e= taum(i) * pm(i)*M(i);
eqAgE(i)..    AgE(i)  =e= cage(i) * (sum(n,Td(n)) + sum(j,Tz(j)) + sum(j,Tm(j)));
eqAgH(l)..    AgH(l)  =e= cagh(l) * (sum(n,Td(n)) + sum(j,Tz(j)) + sum(j,Tm(j)));
* ahorro
* No se tienen en cuenta los Alp para el ahorro destinado a inversión
eqSp(l)..     Sp(l)   =e= ssp(l) * (sum(h, pf(h) * FF(l,h)) + PssH0(l));
eqSg..        Sg      =e= ssg * (sum(l,Td(l)) + sum(j,Tz(j)) + sum(j,Tm(j)) - sum(j,AgE(j)) - sum(l,AgH(l)));
eqXg(i)..     Xg(i)   =e= mu(i) * (sum(l,Td(l)) + sum(j,Tz(j)) + sum(j,Tm(j)) - Sg - sum(j,AgE(j)) - sum(l,AgH(l)))/pq(i);
eqctzsse(i).. CssE(i) =e= ctzsse(i) * F['L',i];
* se cotiza a la seguridad social por los Alp
eqctzssh(l).. CssH(l) =e= ctzssh(l) * (FF[l,'L'] + Alp[l,'l']);
* inversión
eqXv(i)..     Xv(i)   =e= lambda(i) * (sum(l,Sp(l)) + Sg + epsilon*Sf) / pq(i);
* consumo de los hogares, con solo las rentas iniciales (FF) sin el Alp
eqXp(l,i)..   Xp(l,i) =e= alpha(l,i) * (sum(h,pf(h) * FF(l,h)) + AgH(l) + PssH0(l) - (Sp(l) + Td(l)+CssH(l))) / pq(i) + DeAd(l,i);
* producto de Armington
eqpqs(i)..   Q(i)     =e=  gamma(i) * (deltam(i) * M(i) ** eta(i) + deltad(i) * D(i) ** eta(i)) ** (1 / eta(i));
eqM(i)..     M(i)     =e= (gamma(i) ** eta(i) * deltam(i) * pq(i) / ((1 + taum(i)) * pm(i))) ** (1 / (1 - eta(i))) * Q(i);
eqD(i)..     D(i)     =e= (gamma(i) ** eta(i) * deltad(i) * pq(i) / pd(i)) ** (1 / (1 - eta(i))) * Q(i);
* función de transformacion CET
eqpzd(i)..   Z(i)     =e=  theta(i) * (xie(i) * E(i) ** phi(i) + xid(i) * D(i) ** phi(i)) ** (1 / phi(i));
eqE(i)..     E(i)     =e= (theta(i) ** phi(i) * xie(i) * (1 + tauz(i) + CssE(i) / Z(i) - AgE(i) / Z(i) + Apz) * pz(i) / pe(i) )** (1 / (1 - phi(i))) * Z(i);
eqDs(i)..    D(i)     =e= (theta(i) ** phi(i) * xid(i) * (1 + tauz(i) + CssE(i) / Z(i) - AgE(i) / Z(i) + Apz) * pz(i) / pd(i)) ** (1 / (1 - phi(i))) * Z(i);

* el Alp es la diferencia entre las utilizaciones de los sectores (F) y las aportaciones iniciales de los hogares (FF)
eqAlp(l,h).. Alp(l,h) =e= sum(i,F(h,i)) * rf(l,h) - FF(l,h);

* condición de equilibrio del mercado

eqpqd(i)..   Q(i)     =e= sum(l, Xp(l,i)) + Xg(i) + Xv(i) + sum(j, X(i,j));
* es redundante, porque hemos definido Alp como la diferencia entre las utilizaciones de los sectores (F) y las aportaciones iniciales de los hogares (FF)
*eqpf(h)..    sum(i,F(h,i)) =e= sum(l,FF(l,h)) + sum(l,Alp(l,h));

* función objetivo ficticia
*obj..       UU        =e= sum(l, prod(i, Xp(l,i) ** alpha(l,i))) - 100000. * Apz * Apz;
* función objetivo ficticia, con la condición de que el uso de factores sea mínimo (resten lo mínimo)
obj..       UU        =e= sum(l, prod(i, Xp(l,i) ** alpha(l,i))) - 100000. * Apz * Apz - sum(j,F('L',j)) - sum(j,F('K',j));

* inicialización de variables
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
AgE.l(i)  = AgE0(i);
AgH.l(l)  = AgH0(l);
Alp.l(l,h)= Alp0(l,h);
Apz.l     = 0;

* cota inferior de las variables, puede eliminar o producir infactibilidad, según el caso
Y.lo(j)     = 0.0000;
F.lo(h,j)   = 0.0000;
X.lo(i,j)   = 0.0000;
Z.lo(j)     = 0.0000;
Xp.lo(l,i)  = 0.0000;
Xg.lo(i)    = 0.0000;
Xv.lo(i)    = 0.0000;
E.lo(i)     = 0.0000;
M.lo(i)     = 0.0000;
Q.lo(i)     = 0.0000;
D.lo(i)     = 0.0000;
pf.lo(h)    = 0.0000;
py.lo(j)    = 0.0000;
pz.lo(j)    = 0.0000;
pq.lo(i)    = 0.0000;
pe.lo(i)    = 0.0000;
pm.lo(i)    = 0.0000;
pd.lo(i)    = 0.0000;
epsilon.lo  = 0.0000;
Sp.lo(l)    = 0.0000;
Sg.lo       = 0.0000;
Td.lo(l)    = 0.0000;
Tz.lo(j)    = 0.0000;
Tm.lo(i)    = 0.0000;
CssH.lo(l)  = 0.0000;
CssE.lo(i)  = 0.0000;
AgE.lo(i)   = 0.0000;
AgH.lo(l)   = 0.0000;
Alp.lo(l,h) = 0.0000;

* precio de referencia

pf.fx('L') = 1.;
pf.fx('K') = 1.;
epsilon.fx = 1.;

Model mca / all /;


option nlp=CONOPT;
solve mca maximizing UU using nlp;

* salvar a un fichero para después exportar (manualmente) a excel

execute_unload 'base_excel.gdx'
   Y.l,F.l,FF,X.l,Z.l,Xp.l,Xg.l,Xv.l,E.l,M.l,Q.l,D.l,pf.l,py.l,pz.l,pq.l,pe.l,pm.l,pd.l,epsilon,
   Sp.l,Sg.l,Td.l,Tz.l,Tm.l,CssH.l,CssE.l,PssH0,AgE.l,AgH.l,Apz.l,Sf,
   alpha,beta,b,ax,ay,mu,lambda,deltam,deltad,gamma,xid,xie,theta,ssp,ssg,taud,tauz,taum,ctzsse,ctzssh,cage,cagh
;

* bienestar económico
Parameter
   UU0(l) 'nivel de utilidad en el equilibrio de base'
   ep0(l) 'gasto en el equilibrio de base'
   ep1(l) 'gasto en el equilibrio del nuevo escenario'
   EV(l)  'variación equivalente de Hicksian'
;

UU0(l) = prod(i, Xp0(l,i)**alpha(l,i));
ep0(l) = UU0(l) /prod(i, (alpha(l,i)/1)**alpha(l,i));
ep1(l) = (prod(i,Xp.l(l,i)**alpha(l,i))) / prod(i, (alpha(l,i)/1)**alpha(l,i));
EV(l)  = ep1(l) - ep0(l);

display EV;

* -----------------------------------------------------------------------------
* Escenario 1. desde precios 0.5
* -----------------------------------------------------------------------------

pf.l(h)   = 0.5;
py.l(j)   = 0.5;
pz.l(j)   = 0.5;
pq.l(i)   = 0.5;
pe.l(i)   = 0.5;
pm.l(i)   = 0.5;
pd.l(i)   = 0.5;
epsilon.l = 0.5;

* redefinir las cotas inferiores, si no se hace, termina en infactible

pf.lo(h)    = 0.0000;
py.lo(j)    = 0.0000;
pz.lo(j)    = 0.0000;
pq.lo(i)    = 0.0000;
pe.lo(i)    = 0.0000;
pm.lo(i)    = 0.0000;
pd.lo(i)    = 0.0000;
epsilon.lo  = 0.0000;

* precio de referencia
pf.fx('L') = 1.;
pf.fx('K') = 1.;
epsilon.fx = 1.;

* inicia el solver desde el principio
option bRatio = 1;

option nlp=CONOPT;

* resuelve mca maximizando UU mediante nlp;
solve mca maximizing UU using nlp;

execute_unload 'precios_excel.gdx'
   Y.l,F.l,FF,X.l,Z.l,Xp.l,Xg.l,Xv.l,E.l,M.l,Q.l,D.l,pf.l,py.l,pz.l,pq.l,pe.l,pm.l,pd.l,epsilon,
   Sp.l,Sg.l,Td.l,Tz.l,Tm.l,CssH.l,CssE.l,PssH0,AgE.l,AgH.l,Apz.l,Sf,
   alpha,beta,b,ax,ay,mu,lambda,deltam,deltad,gamma,xid,xie,theta,ssp,ssg,taud,tauz,taum,ctzsse,ctzssh,cage,cagh,
   Alp.l
;


* -----------------------------------------------------------------------------
* Escenario 2. 1000 demanda adicional de AP3 por C2
* -----------------------------------------------------------------------------

* precios de referencia
pf.fx('L') = 1.;
pf.fx('K') = 1.;
epsilon.fx = 1.;

DeAd('C2','AP3') = 1000.

display FF,F0,Y0,X0,Xp0,Xg0,Xv0,Q0,Z0,E0,M0,D0,Tz0,Tm0,Sp0,Td0,AgE0,AgH0,Sg0,Sf,
        CssE0,CssH0,PssH0,Alp0,DeAd;

* inicia el solver desde el principio
option bRatio = 1;

option nlp=CONOPT;

* resuelve mca maximizando UU mediante nlp;
solve mca maximizing UU using nlp;

execute_unload 'demanda_excel.gdx'
   Y.l,F.l,FF,X.l,Z.l,Xp.l,Xg.l,Xv.l,E.l,M.l,Q.l,D.l,pf.l,py.l,pz.l,pq.l,pe.l,pm.l,pd.l,epsilon,
   Sp.l,Sg.l,Td.l,Tz.l,Tm.l,CssH.l,CssE.l,PssH0,AgE.l,AgH.l,Apz.l,Sf,
   alpha,beta,b,ax,ay,mu,lambda,deltam,deltad,gamma,xid,xie,theta,ssp,ssg,taud,tauz,taum,ctzsse,ctzssh,cage,cagh,
   Alp.l
;
