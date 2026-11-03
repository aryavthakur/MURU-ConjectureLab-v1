# Draft analytical chemistry review request

**Not sent. Recipient and sharing approval remain pending.**

Subject: Request for technical feedback on collision-energy interpretation in an internal MS/MS modeling study

Dear Dr. [Name],

I am Aryav Thakur, lead developer of MURU-ConjectureLab. I have prepared an internal computational study of a scalar fragmentation-extent prediction target using WUR development data and a one-time MSnLib external evaluation. I am seeking technical feedback from someone experienced with tandem mass spectrometry, instrument energy conventions, or fragmentation modeling.

The main issue is specific. The frozen project protocol labels the MSnLib settings as NCE 20 and 60. The peer-reviewed MSnLib paper describes the Orbitrap ID-X MS2 settings as 20 eV and 60 eV. The nine source archives used for this analysis do not include native method records resolving which convention applies to each selected file. The external deployment adapter assumed ID-X NCE equaled IQ-X NCE, and the prespecified anchor agreement gate failed at A0, A1, and A2. The model comparison is numerically reproducible under the frozen adapter, but physical energy transfer is not established.

Would you be willing to assess the attached technical packet, especially whether the units are interpreted correctly, what the fixed adapter can mean physically, whether the anchor results materially narrow the primary comparison, and what evidence is needed for any stronger transfer claim? The packet also summarizes the endpoint, precursor-including μ, model-specific comparator inputs, and limitations. We request critical scientific feedback, not approval or a formal journal review.

This is an unpublished internal AI-assisted manuscript. No journal submission has been made. If you are interested, I can share the packet after confirming the distribution scope and any applicable data-rights notices. No raw spectra or restricted source data are included in the current packet.

Best,
Aryav Thakur
MURU-ConjectureLab
[Contact address to be supplied by author]
