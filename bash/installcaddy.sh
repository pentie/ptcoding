#!/bin/bash

if ! id www-data; then
  groupadd --system www-data
  useradd -g www-data --no-user-group --home-dir /var/www --shell /usr/sbin/nologin --system www-data
fi
mkdir -p /etc/ssl/caddy /etc/caddy/
chown root:www-data -R /etc/ssl/caddy 
chmod 0770 /etc/ssl/caddy

curl https://getcaddy.com | bash -s personal
(base64 -d | gunzip -c > "/etc/systemd/system/caddy.service") <<EOF
H4sICOVfuV0AA2NhZGR5LnNlcnZpY2UAdVbtbts2FP2vp7grBnQDYqsp2n0F+pHE2WKscb3YWTEURUuJVxYRitRIyqr+7Wn2YHuSHVJ21mwrECCxdXl47jnnXuXtnVHhXbZgXznVBWVNcSmkHOl6u13nz2ngkjy7PbtsYau+ZRNEqmpC6PwPeV7F6qliXtk2l7by2Xkd2BWGw2Dd/cwarQzPg3A7DtkbYYL//2fkRx+4lbPDUzkbhArHmniJqjjL3m6mv95lt+xxMhTWzERprGuFzrIzWlgyNpDQ2g4UGqbO2Yq9p2CpZHLTKZakDAkKatcE0tZ2c1rWsR4QxxO1UDqdS0dOyNuWQ6PMjqBXUJXQZJjlEbpWH1nOs00sfqVaFZYGSuyF3nBVnL548ezZJ88ueudDcfosUr5DdySMpJ2zffeI9KC0JteDqp9nsa4YhmEmRRDZT7H4n4/AecXBs6nc2IWZ8r5HkxW7oGpQDXwAA9EB7AObSBvteJLKcRWsG+fZldkrZ020urg8Xyx+W59vr4ucQ5V7ryfD41XnehCjRzoCPZk5a8OTpNODQF7UHBWuhMfvQDAYelq3s+lmPIldprTVSjMu/shVUqfIe+9ybaFuXiozXUkzbQEapO0DzcTOMRfB9Uyzypp64pcK8wdISrSKfC9cHtouXXDL2gpZJNz7KMbsbnN7Sl/enC9X6+Xi4AVsEBXXvSbf9LhyMFAuNEiLY+GtESXQg2oZZLKfAXNjJRdtdD993KidEbrYLH/65W65zbZT5SbYLgbhpU9WxQwkDUzflrDf1pRYy8MwWufPIC/Th1aY42zMGU18iDpSax2TTigwIUBzBCShrl7/uHx1hWi9+O7lt9/ElkxrJUIQ45DEhOVxRPhjB9vxLZzr0XaCDI2I3ohwRFvfvr4sXp4+P4rTObVHmiiKmkJ7VPiEhkZVkAkoUvlKOAlsEbfB4V4PCcByPSFs2y55eMAV1CqjMMSUS97TVzdipNLFLOGsimsHjzxXPcKLFmryMKVqJvpPI9DTEyoRDyjS4mzsMO4RsoZuhe8gshtprZ56gnwW0juIHVeJj5MdjzXCYzwQT9CPJsspp2lCfJh/fWS+mI4VtdA+0r9WEno0CP8J5TF1J5MwmFuEGbuRVra0ECANIJxEJ6PtHW0217N7HpMmNsCMa2AcRbkR90DFMAC0TKAx5gm5s96rUo9p4CbfaqslOx8jKuPSHB8wNyk7BfKsgfrXH3/C+Iq7QI+nGuJxJWIOBvxgTz9aJ4/2SNQOI3tGRNuoTouPIOM4CGVAIR9IVGl9ubheoS/ElZan2OEyNAGDeJjTTe8R4PDJYkrTZaf90FgfvsCiF/INnvBahMb/exk9PF0ctpji/9SA6rZJGuGl8LlITVtQ7UEz6jeFJw3+Yfpo//z59zE8Giq4+QQ6Ut27FKb4ZnGqCmlCMMq7pJQICL+Jze0gDiJVjtM0zDGXeGfGTRvTjDxgnO+TrCv4Nh2N38YwN2LPMedRu0p0olQa/Dna/XsP3gk2itrpfhc9QHBhJcAuj9Xjhe2NRPMbjqt9/X51tX1/sVwt3m+ubn9dXl5lZ+dtqUDn8pMLPlO5sise1g99TpHN3i4N3pRav0vveZYXY9H2OqhZGoLDvwB/A3GAsiZ1CAAA
EOF
base64 -d > "/etc/systemd/system/v2""ra""y.service" <<EOF
W1VuaXRdCkRlc2NyaXB0aW9uPVYyUmF5IFNlcnZpY2UKQWZ0ZXI9bmV0d29yay50YXJnZXQKV2Fu
dHM9bmV0d29yay50YXJnZXQKCltTZXJ2aWNlXQpUeXBlPXNpbXBsZQpVc2VyPXd3dy1kYXRhCkdy
b3VwPXd3dy1kYXRhClBJREZpbGU9L3J1bi92MnJheS5waWQKRXhlY1N0YXJ0PS91c3IvYmluL3Yy
cmF5L3YycmF5IC1jb25maWcgL2V0Yy92MnJheS9jb25maWcuanNvbgpSZXN0YXJ0PW9uLWZhaWx1
cmUKUmVzdGFydFByZXZlbnRFeGl0U3RhdHVzPTIzCgpbSW5zdGFsbF0KV2FudGVkQnk9bXVsdGkt
dXNlci50YXJnZXQK
EOF
systemctl daemon-reload
