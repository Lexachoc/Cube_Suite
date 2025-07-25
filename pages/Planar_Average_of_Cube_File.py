import streamlit as st
import platform
import tempfile
import os
import py3Dmol
import streamlit.components.v1 as components
import subprocess
import sys
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Set page config
st.set_page_config(page_title='Cube Suite - A web app (GUI) for Cube Toolz', layout='wide', page_icon="🧊",
                   menu_items={'About': "A web app to help you process CUBE files generated by quantum chemistry programs. Powered by [CUBE TOOLZ](https://github.com/funkymunkycool/Cube-Toolz/tree/master)"
                   })

# Sidebar stuff
st.sidebar.write('# About')
st.sidebar.write('Originally Made By [Manas Sharma](https://manas.bragitoff.com)')
st.sidebar.write('### *Powered by*')
st.sidebar.write('* [Cube Toolz](https://github.com/funkymunkycool/Cube-Toolz/tree/master) for manipulating and processing cube files')
st.sidebar.write('* [Py3Dmol](https://3dmol.csb.pitt.edu/) for Cube File Visualizations')
st.sidebar.write('* [Streamlit](https://streamlit.io/) for making of the Web App')
# st.sidebar.write('* [PyMatgen](https://pymatgen.org/) for Periodic Structure Representations')
# st.sidebar.write('* [PubChempy](https://pypi.org/project/PubChemPy/1.0/) for Accessing the PubChem Database')
# st.sidebar.write('* [ASE](https://wiki.fysik.dtu.dk/ase/) for File Format Conversions')
st.sidebar.write('### *Contributors*')
st.sidebar.write('[Ya-Fan Chen ](https://github.com/Lexachoc)')
st.sidebar.write('### *Source Code*')
st.sidebar.write('[GitHub Repository](https://github.com/manassharma07/Cube_Suite)')


def display_cube_file(file_content_text, viz1_html_name, isovalue, opacity):
    # Py3Dmol visualization code
    spin = st.checkbox('Spin', value=False, key='key' + 'viz1.html')
    view = py3Dmol.view(width=500, height=400)
    view.addModel(file_content_text, 'cube')
    view.setStyle({'sphere': {'colorscheme': 'Jmol', 'scale': 0.3}, 'stick': {'colorscheme': 'Jmol', 'radius': 0.2}})
    view.addUnitCell()

    # Negative lobe
    view.addVolumetricData(file_content_text, 'cube', {'isoval': -abs(isovalue), 'color': 'blue', 'opacity': opacity})

    # Positive lobe
    view.addVolumetricData(file_content_text, 'cube', {'isoval': abs(isovalue), 'color': 'red', 'opacity': opacity})

    view.zoomTo()
    view.spin(spin)
    view.setClickable({'clickable': 'true'})
    view.enableContextMenu({'contextMenuEnabled': 'true'})
    view.show()
    view.render()

    t = view.js()
    f = open(viz1_html_name, 'w')
    f.write(t.startjs)
    f.write(t.endjs)
    f.close()

    HtmlFile = open(viz1_html_name, 'r', encoding='utf-8')
    source_code = HtmlFile.read()
    components.html(source_code, height=300, width=500)
    HtmlFile.close()


# New feature since streamlit v1.33.0
@st.fragment
def show_download_button(df):
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name='planar_average.csv',
        mime='text/csv',
    )


# Main app
# st.header('Cube Suite')
# st.write('##### A web app to help you process CUBE files generated by quantum chemistry programs. Powered by [CUBE TOOLZ](https://github.com/funkymunkycool/Cube-Toolz/tree/master).')

st.write('### Calculate Planar Average (also referred to as Planar Integrated)')
st.write('For example, if the cube file contains density then the planar averaged density (planar integrated charge density) along a given direction (say **z**) is given as')
st.latex('\\tilde{\\rho}(z)=\int\\rho(x,y,z){dxdy}')
st.write('with $\\tilde{\\rho}(z)$ having the unit of $e/\mathrm{\AA}$')

# File uploader
uploaded_file = st.file_uploader("Choose a .cub or .cube file", type=[".cub", ".cube"])

# If the button is clicked and a file is uploaded
if uploaded_file is not None:
    # Read the file content as text
    file_content_text = uploaded_file.read().decode()

    temp_dir = tempfile.mkdtemp()
    filepath = os.path.join(temp_dir, uploaded_file.name)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getvalue())

    # Dropdown to select the axis
    axis = st.selectbox('Select Axis', ['x', 'y', 'z'])

    # Button to calculate planar average
    calculate_planar_average = st.button('Calculate Planar Average')
    if calculate_planar_average:
        # Run the cube_tools command to calculate planar average
        result = subprocess.run(["cube_tools", "-m", axis, filepath], capture_output=True, text=True)

        if result.stderr:
            st.write("Error:", result.stderr)
        else:
            # Read the output data from the generated 'mean.dat' file
            with open('planav.dat', 'r') as f:
                data = [line.strip().split() for line in f.readlines()]

            # Extract x (distance) and y (planar average) values
            x_values = [float(row[0]) for row in data]
            y_values = [float(row[1]) for row in data]

            # Calculate the integrated planar density
            integrated_density = []
            total_integrated_density = 0.0
            for i in range(len(x_values) - 1):
                dx = x_values[i + 1] - x_values[i]
                y = y_values[i]
                integrated_density.append(dx * y)
                total_integrated_density += dx * y
            integrated_density.append(0.0)

            # Create a pandas DataFrame for display as a table

            df = pd.DataFrame({
                'Distance (' + axis + ')': x_values,
                'Planar Averaged Density': y_values,
                'd' + axis + '*(planar average density)': integrated_density
            })

            # Display the table
            st.write('Planar Average Data:')
            st.write(df)

            # Show the total integrated density
            st.write(f'Total number of electrons from integrating planar averaged density: {total_integrated_density:.6f}')
            result = subprocess.run(["cube_tools", "-i", filepath], capture_output=True, text=True)
            st.write(" " + str(result.stdout))
            if result.stderr:
                st.write("Error:", result.stderr)
            # st.write(f'Total number of electrons from integrating the entire cube file: {total_integrated_density:.6f}')

            # Plot the planar averaged density
            st.subheader('Planar Averaged Density Plot')

            fig = px.scatter(df,
                             x='Distance (' + axis + ')',
                             y='Planar Averaged Density',
                             title=f'Planar Averaged Density vs Distance'
                             )
            fig.update_traces(mode='lines+markers', marker={'size': 8})
            fig.update_traces(
                hovertemplate="<br>".join([
                    "Distance=%{x}", "Planar averaged density=%{y}"
                ])
            )
            fig.update_layout(
                title_font_size=18,
                xaxis_title_font_size=18,
                yaxis_title_font_size=18,
                xaxis=dict(
                    tickfont=dict(size=15),
                ),
                yaxis=dict(
                    tickfont=dict(size=15),
                    showexponent='last',
                    exponentformat='e',
                ),

                hoverlabel=dict(font=dict(size=15))
            )

            # Use Plotly
            # see: https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart#stplotly_chart
            st.plotly_chart(fig,
                            on_select="ignore",
                            key="scatter_chart"
                            )

            # BUG: Dataframe will disappear after clicking on download. This is due to the design of Streamlit, which reloads the app.
            # see: https://github.com/streamlit/streamlit/issues/4382
            # see: https://github.com/streamlit/streamlit/issues/3832
            # a temporary workaround: https://github.com/streamlit/streamlit/issues/4382#issuecomment-2040559079
            # or use session state to restore the dataframe:
            # https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state

            # Download button for the data as CSV
            show_download_button(df)
